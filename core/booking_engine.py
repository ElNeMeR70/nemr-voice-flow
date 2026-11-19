"""
Nemr Voice Flow - SQLite-Backed Appointment & Booking Engine (v2.0.0)
Supports slot conflict detection, available slot listing, cancellation, and SQLite/MySQL persistence.
"""

from __future__ import annotations
import datetime
import sqlite3
from dataclasses import dataclass
from typing import List


@dataclass
class BookingRecord:
    id: int
    customer_phone: str
    customer_name: str
    service: str
    booking_date: str
    status: str = "confirmed"
    duration_minutes: int = 30


class BookingEngine:
    """Manages conversational booking slots with SQLite persistence & overlap protection."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_phone TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                service TEXT NOT NULL,
                booking_date TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL DEFAULT 30,
                status TEXT NOT NULL DEFAULT 'confirmed',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self._conn.commit()

    @property
    def bookings(self) -> List[BookingRecord]:
        cur = self._conn.execute(
            "SELECT id, customer_phone, customer_name, service, booking_date, status, duration_minutes FROM voice_bookings ORDER BY id ASC"
        )
        return [
            BookingRecord(
                id=row[0],
                customer_phone=row[1],
                customer_name=row[2],
                service=row[3],
                booking_date=row[4],
                status=row[5],
                duration_minutes=row[6],
            )
            for row in cur.fetchall()
        ]

    @staticmethod
    def _parse_dt(date_str: str) -> datetime.datetime:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        raise ValueError(f"Unsupported datetime format: {date_str}")

    def create_booking(
        self,
        customer_phone: str,
        customer_name: str,
        service: str,
        date_str: str,
        duration_minutes: int = 30,
    ) -> BookingRecord:
        req_start = self._parse_dt(date_str)
        req_end = req_start + datetime.timedelta(minutes=duration_minutes)

        # Check active confirmed bookings for time overlap
        for existing in self.bookings:
            if existing.status != "confirmed":
                continue
            ex_start = self._parse_dt(existing.booking_date)
            ex_end = ex_start + datetime.timedelta(minutes=existing.duration_minutes)
            if req_start < ex_end and ex_start < req_end:
                raise ValueError(f"Time slot conflict with booking #{existing.id} at {existing.booking_date}")

        canonical_dt = req_start.strftime("%Y-%m-%d %H:%M:%S")
        cur = self._conn.execute(
            """
            INSERT INTO voice_bookings (customer_phone, customer_name, service, booking_date, duration_minutes, status)
            VALUES (?, ?, ?, ?, ?, 'confirmed')
            """,
            (customer_phone, customer_name, service, canonical_dt, duration_minutes),
        )
        self._conn.commit()

        return BookingRecord(
            id=cur.lastrowid or 0,
            customer_phone=customer_phone,
            customer_name=customer_name,
            service=service,
            booking_date=canonical_dt,
            status="confirmed",
            duration_minutes=duration_minutes,
        )

    def cancel_booking(self, booking_id: int) -> bool:
        cur = self._conn.execute(
            "UPDATE voice_bookings SET status = 'cancelled' WHERE id = ? AND status = 'confirmed'",
            (booking_id,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def get_available_slots(
        self,
        date_yyyy_mm_dd: str,
        start_hour: int = 10,
        end_hour: int = 18,
        slot_minutes: int = 30,
    ) -> List[str]:
        day_start = datetime.datetime.strptime(date_yyyy_mm_dd.strip(), "%Y-%m-%d")
        cursor_dt = day_start.replace(hour=start_hour, minute=0, second=0)
        end_dt = day_start.replace(hour=end_hour, minute=0, second=0)

        confirmed_windows = [
            (
                self._parse_dt(b.booking_date),
                self._parse_dt(b.booking_date) + datetime.timedelta(minutes=b.duration_minutes),
            )
            for b in self.bookings
            if b.status == "confirmed"
        ]

        available: List[str] = []
        step = datetime.timedelta(minutes=slot_minutes)
        while cursor_dt + step <= end_dt:
            slot_end = cursor_dt + step
            overlaps = any(cursor_dt < ex_end and ex_start < slot_end for ex_start, ex_end in confirmed_windows)
            if not overlaps:
                available.append(cursor_dt.strftime("%Y-%m-%d %H:%M:%S"))
            cursor_dt += step

        return available

    def close(self) -> None:
        self._conn.close()

    def get_sql_schema(self) -> str:
        return """CREATE TABLE IF NOT EXISTS `voice_bookings` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `customer_phone` VARCHAR(30) NOT NULL,
  `customer_name` VARCHAR(150) NOT NULL,
  `service` VARCHAR(150) NOT NULL,
  `booking_date` DATETIME NOT NULL,
  `duration_minutes` INT NOT NULL DEFAULT 30,
  `status` VARCHAR(50) NOT NULL DEFAULT 'confirmed',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_phone` (`customer_phone`),
  INDEX `idx_booking_date` (`booking_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"""
