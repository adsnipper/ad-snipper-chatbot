import json
from pathlib import Path
from typing import Any

import gspread
from gspread.exceptions import GSpreadException
from google.oauth2.service_account import Credentials

from app.config import Settings
from app.models import ChatMessage, LeadRecord


class SheetsService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = None
        self.spreadsheet = None

        if settings.google_sheets_spreadsheet_id and (
            settings.google_sheets_credentials_json or settings.google_sheets_credentials_file
        ):
            try:
                info = self._load_credentials_info()
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
                credentials = Credentials.from_service_account_info(info, scopes=scopes)
                self.client = gspread.authorize(credentials)
                self.spreadsheet = self.client.open_by_key(settings.google_sheets_spreadsheet_id)
            except (GSpreadException, OSError, json.JSONDecodeError, ValueError) as exc:
                print(f"[Sheets disabled] Could not initialize Google Sheets: {exc}")

    def _load_credentials_info(self) -> dict:
        if self.settings.google_sheets_credentials_json:
            return json.loads(self.settings.google_sheets_credentials_json)
        path = Path(self.settings.google_sheets_credentials_file)
        return json.loads(path.read_text(encoding="utf-8"))

    @property
    def enabled(self) -> bool:
        return self.spreadsheet is not None

    def _append(self, tab_name: str, row: list[Any]) -> None:
        if not self.enabled:
            print(f"[Sheets disabled] {tab_name}: {row}")
            return
        try:
            worksheet = self.spreadsheet.worksheet(tab_name)
            worksheet.append_row(row, value_input_option="USER_ENTERED")
        except GSpreadException as exc:
            print(f"[Sheets error] Could not append to {tab_name}: {exc}")

    def _find_lead_row(self, conversation_id: str) -> int | None:
        if not self.enabled:
            return None
        try:
            worksheet = self.spreadsheet.worksheet(self.settings.google_sheets_leads_tab)
            records = worksheet.get_all_records()
            for index, record in enumerate(records, start=2):
                if record.get("Conversation ID") == conversation_id:
                    return index
        except GSpreadException as exc:
            print(f"[Sheets error] Could not find lead row: {exc}")
        return None

    def append_lead(self, lead: LeadRecord) -> None:
        row = [
            lead.timestamp.isoformat(),
            lead.name,
            lead.email,
            lead.whatsapp,
            lead.source_page,
            lead.country,
            lead.device,
            lead.chat_started.isoformat() if lead.chat_started else "",
            lead.chat_ended.isoformat() if lead.chat_ended else "",
            lead.message_count,
            lead.intent_score,
            "Yes" if lead.calendly_booked else "No",
            lead.meeting_date or "",
            lead.conversation_id,
        ]
        if not self.enabled:
            print(f"[Sheets disabled] {self.settings.google_sheets_leads_tab}: {row}")
            return

        try:
            worksheet = self.spreadsheet.worksheet(self.settings.google_sheets_leads_tab)
            existing_row = self._find_lead_row(lead.conversation_id)
            if existing_row:
                worksheet.update(f"A{existing_row}:N{existing_row}", [row], value_input_option="USER_ENTERED")
                return
            worksheet.append_row(row, value_input_option="USER_ENTERED")
        except GSpreadException as exc:
            print(f"[Sheets error] Could not write lead row: {exc}")

    def append_conversation_message(self, conversation_id: str, email: str, message: ChatMessage) -> None:
        self._append(
            self.settings.google_sheets_conversations_tab,
            [
                conversation_id,
                message.timestamp.isoformat(),
                "Bot" if message.role == "assistant" else "User",
                message.content,
                email,
            ],
        )

    def update_booking_status(self, conversation_id: str, booked: bool, meeting_date: str) -> None:
        if not self.enabled:
            print(
                f"[Sheets disabled] Update booking for {conversation_id}: booked={booked}, meeting_date={meeting_date}"
            )
            return

        row_index = self._find_lead_row(conversation_id)
        if row_index is None:
            return
        try:
            worksheet = self.spreadsheet.worksheet(self.settings.google_sheets_leads_tab)
            worksheet.update(f"L{row_index}:M{row_index}", [["Yes" if booked else "No", meeting_date]])
        except GSpreadException as exc:
            print(f"[Sheets error] Could not update booking status: {exc}")