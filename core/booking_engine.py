"""
Nemr Voice Flow - Structured Appointment & Booking Engine
Validates slot availability, persists client bookings, and generates confirmations.
"""

from __future__ import annotations
import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class BookingRecord:
    id: int
    customer_phone: str
    customer_name: str
    service: str
    booking_date: str
    status: str = "confirmed"


class BookingEngine:
    """Manages conversational booking slots and database records."""

    def __init__(self):
        self.bookings: List[BookingRecord] = []
        self._next_id = 1

    def create_booking(
        self,
        customer_phone: str,
        customer_name: str,
        service: str,
        date_str: str
    ) -> BookingRecord:
        record = BookingRecord(
            id=self._next_id,
            customer_phone=customer_phone,
            customer_name=customer_name,
            service=service,
            booking_date=date_str,
            status="confirmed"
        )
        self.bookings.append(record)
        self._next_id += 1
        return record

    def get_sql_schema(self) -> str:
        return """CREATE TABLE IF NOT EXISTS `voice_bookings` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `customer_phone` VARCHAR(30) NOT NULL,
  `customer_name` VARCHAR(150) NOT NULL,
  `service` VARCHAR(150) NOT NULL,
  `booking_date` DATETIME NOT NULL,
  `status` VARCHAR(50) NOT NULL DEFAULT 'confirmed',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_phone` (`customer_phone`),
  INDEX `idx_booking_date` (`booking_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"""
