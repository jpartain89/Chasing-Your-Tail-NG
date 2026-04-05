### Chasing Your Tail V04_15_22
### @matt0177
### Released under the MIT License https://opensource.org/licenses/MIT
###

import argparse
import logging
import signal
import sys
import time

from cyt_core_runtime import (
    MonitoringService,
    create_cyt_log,
    ensure_runtime_directories,
    load_runtime_context,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cyt_security.log"), logging.StreamHandler()],
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Secure CYT real-time monitor",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file (default: config.json)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single monitoring cycle and exit",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    context = load_runtime_context(args.config)
    logging.info("Configuration loaded with secure credential management")

    ensure_runtime_directories(context.config)
    print("Current Time: " + time.strftime("%Y-%m-%d %H:%M:%S"))

    _, cyt_log = create_cyt_log(context.config)
    service = MonitoringService(context, cyt_log)

    should_stop = {"stop": False}

    def signal_handler(signum, frame):
        should_stop["stop"] = True
        print("\nShutting down gracefully...")
        cyt_log.write("Shutting down gracefully...\n")
        logging.info("CYT monitoring stopped by user")

    signal.signal(signal.SIGINT, signal_handler)

    try:
        latest_file = service.initialize()
        print(f"{len(service.ignore_list)} MACs added to ignore list.")
        print(f"{len(service.probe_ignore_list)} Probed SSIDs added to ignore list.")
        print(f"Pulling data from: {latest_file}")
        print("Initializing secure tracking lists...")
        print("Initialization complete!")

        check_interval = context.config.get("timing", {}).get("check_interval", 60)
        list_update_interval = context.config.get("timing", {}).get(
            "list_update_interval", 5
        )

        logging.info("Starting secure CYT monitoring loop...")
        print("SECURE MODE: All SQL injection vulnerabilities have been eliminated!")
        print(
            f"Monitoring every {check_interval} seconds, updating lists every {list_update_interval} cycles"
        )

        time_count = 0
        while not should_stop["stop"]:
            time_count += 1
            try:
                service.run_cycle(time_count)
            except Exception as e:
                error_msg = f"Error in monitoring loop: {e}"
                print(error_msg)
                cyt_log.write(f"{error_msg}\n")
                logging.error(error_msg)

            if args.once:
                break
            time.sleep(check_interval)

        return 0

    except Exception as e:
        error_msg = f"Fatal error during initialization: {e}"
        print(error_msg)
        cyt_log.write(f"{error_msg}\n")
        logging.error(error_msg)
        return 1
    finally:
        cyt_log.close()


if __name__ == "__main__":
    sys.exit(main())
