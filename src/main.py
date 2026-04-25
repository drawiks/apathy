import logging
import config
from bot import ApathyBot


def main() -> None:
    if not config.BOT_TOKEN:
        logging.error("BOT_TOKEN not found in .env")
        return
    
    logging.info("starting")
    
    bot = ApathyBot()
    bot.run(config.BOT_TOKEN)


if __name__ == "__main__":
    main()