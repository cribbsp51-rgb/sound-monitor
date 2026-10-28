#!/usr/bin/env python3

import time
from pathlib import Path
from datetime import datetime

from meter.pcbartists_meter import PCBArtistsMeter
from exporters.csv_exporter import CSVExporter
from exporters.sqlite_exporter import SQLiteExporter
from utils.jsonl import log_jsonl
import config.settings as cfg

# Optional camera support
if cfg.CAMERA_ENABLED:
    from camera.capture import capture_image


def daily_log_file(base_file):
    """
    Example:

        data/sound_evidence.csv

    becomes

        data/sound_evidence_2026-10-12.csv
    """

    p = Path(base_file)

    date_str = datetime.now().strftime("%Y-%m-%d")

    return str(
        p.with_name(
            f"{p.stem}_{date_str}{p.suffix}"
        )
    )


def capture_if_enabled(prefix):
    """
    Capture image when camera support is enabled.
    Returns path or None.
    """

    if not cfg.CAMERA_ENABLED:
        return None

    try:
        return capture_image(prefix=prefix)

    except Exception as e:
        print(
            f"⚠️ Camera capture failed: {e}",
            flush=True
        )
        return None


def main():

    current_day = datetime.now().strftime("%Y-%m-%d")

    # Daily CSV file
    csv_out = CSVExporter(
        daily_log_file(cfg.LOG_CSV)
    )

    # Single SQLite database
    sqlite_out = SQLiteExporter(
        cfg.LOG_DB
    )

    event_active = False
    event_start = None
    event_peak = 0.0
    event_image = None

    last_spl = 0.0

    print(
        "Launching PCBA‑DBM‑r3 High-Speed Acoustic Monitor Daemon..."
    )

    if cfg.CAMERA_ENABLED:
        print("Camera Support: ENABLED")
    else:
        print("Camera Support: DISABLED")

    with PCBArtistsMeter() as meter:

        while True:

            # ----------------------------------------------------
            # MIDNIGHT ROLLOVER
            # ----------------------------------------------------
            new_day = datetime.now().strftime("%Y-%m-%d")

            if new_day != current_day:

                print(
                    f"📅 New day detected: {new_day}",
                    flush=True
                )

                current_day = new_day

                csv_out = CSVExporter(
                    daily_log_file(cfg.LOG_CSV)
                )

                print(
                    f"📁 Switched CSV log to "
                    f"{daily_log_file(cfg.LOG_CSV)}",
                    flush=True
                )

            try:
                spl = meter.spl()

            except OSError:

                print(
                    "⚠️ I2C Read Error! Retrying connection...",
                    flush=True
                )

                time.sleep(1.0)
                continue

            except KeyboardInterrupt:
                break

            timestamp_now = datetime.now().isoformat(
                sep=" ",
                timespec="seconds"
            )

            print(
                f"[{timestamp_now}] "
                f"Real-time SPL(A): {int(spl)} dB | "
                f"Active Event: {event_active}",
                flush=True
            )

            # ----------------------------------------------------
            # EARLY CAMERA TRIGGER
            # ----------------------------------------------------
            if (
                cfg.CAMERA_ENABLED and
                last_spl > 0.0 and
                (spl - last_spl >= 3.0) and
                not event_active
            ):

                if event_image is None:

                    event_image = capture_if_enabled(
                        prefix="vehicle_early"
                    )

            # ----------------------------------------------------
            # EVENT START
            # ----------------------------------------------------
            if spl >= cfg.EVENT_THRESHOLD_DB:

                if not event_active:

                    event_active = True
                    event_start = time.time()

                    print(
                        f"🚨 Event Triggered! "
                        f"SPL: {int(spl)} dB threshold crossed.",
                        flush=True
                    )

                    try:
                        meter.clear_minmax()

                    except Exception as e:

                        print(
                            f"⚠️ MIN/MAX clear failed: {e}",
                            flush=True
                        )

                    if event_image is None:

                        event_image = capture_if_enabled(
                            prefix="vehicle_peak"
                        )

                    try:
                        event_peak = meter.spl_max()

                    except Exception:
                        event_peak = spl

                if spl > event_peak:
                    event_peak = spl

            # ----------------------------------------------------
            # EVENT END
            # ----------------------------------------------------
            else:

                if event_active:

                    duration = (
                        time.time() - event_start
                    )

                    ts = datetime.now().isoformat()

                    try:

                        hw_peak = meter.spl_max()

                        if hw_peak >= cfg.EVENT_THRESHOLD_DB:
                            event_peak = hw_peak

                    except Exception:
                        pass

                    try:

                        # Daily JSONL file
                        log_jsonl(
                            daily_log_file(
                                cfg.LOG_JSONL
                            ),
                            {
                                "ts": ts,
                                "spl_peak": event_peak
                            }
                        )

                        # Daily CSV file
                        csv_out.write(
                            ts,
                            event_peak
                        )

                        # Single SQLite database
                        sqlite_out.write_evidence(
                            ts,
                            event_peak
                        )

                        try:

                            history_payload = (
                                meter.get_history_array()
                            )

                        except OSError:
                            history_payload = []

                        sqlite_out.write_event(
                            ts=ts,
                            duration=duration,
                            peak_db=event_peak,
                            history=history_payload,
                            image=event_image
                        )

                        print(
                            f"💾 Event Saved Successfully! "
                            f"Peak: {int(event_peak)} dB | "
                            f"Duration: {duration:.1f}s",
                            flush=True
                        )

                    except Exception as save_err:

                        print(
                            f"⚠️ Telemetry write failed: "
                            f"{save_err}",
                            flush=True
                        )

                    event_active = False
                    event_peak = 0.0
                    event_image = None

            last_spl = spl

            time.sleep(1.0)


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        print(
            "\nAcoustic monitor closed cleanly."
        )
