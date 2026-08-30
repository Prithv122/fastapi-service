"""Enumerations shared across models and schemas."""

from enum import StrEnum


class Sector(StrEnum):
    FINANCIALS = "Financials"
    IT = "IT"
    DEFENCE = "Defence"
    RENEWABLES = "Renewables"
    PHARMA_HEALTHCARE = "Pharma & Healthcare"
    AUTO = "Auto"
    CHEM_METALS_ENG = "Chem/Metals/Eng"
    FMCG = "FMCG"
    INFRA_REALTY = "Infra/Realty"
    POWER_TD = "Power T&D"
    TRADITIONAL_POWER = "Traditional Power"
    TELECOM = "Telecom"
    CONSUMER_RETAIL = "Consumer/Retail"
    MISC = "Misc"


class CallType(StrEnum):
    BUY = "BUY"
    ACCUMULATE = "ACCUMULATE"
    HOLD = "HOLD"
    WAIT_AND_BUY = "WAIT_AND_BUY"
    SELL = "SELL"


class TimeFrame(StrEnum):
    SWING = "SWING"
    POSITIONAL = "POSITIONAL"
    LONG_TERM = "LONG_TERM"


class SetupStatus(StrEnum):
    OPEN = "OPEN"
    TRIGGERED = "TRIGGERED"
    INVALIDATED = "INVALIDATED"
    CLOSED = "CLOSED"


class BrokerName(StrEnum):
    ZERODHA = "ZERODHA"
    GROWW = "GROWW"
    OTHER = "OTHER"


class TradeSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
