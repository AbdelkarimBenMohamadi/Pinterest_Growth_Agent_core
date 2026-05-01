class PGAError(Exception):
    """Base exception for all PGA errors."""
    pass


class ScraperError(PGAError):
    """Raised when scraping fails."""
    pass


class GenerationError(PGAError):
    """Raised when content generation fails."""
    pass


class PostingError(PGAError):
    """Raised when posting to Pinterest fails."""
    pass


class SafetyError(PGAError):
    """Raised when a safety limit is hit."""
    pass


class CooldownError(PGAError):
    """Raised when account is in cooldown."""
    pass
