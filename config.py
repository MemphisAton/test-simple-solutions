from dataclasses import dataclass
from typing import Optional

from environs import Env


@dataclass
class StripeConfig:
    secret_key: str
    publishable_key: str


@dataclass
class DatabaseConfig:
    django_secret_key: str


@dataclass
class Config:
    db: DatabaseConfig
    stripe: StripeConfig


def load_config(path: str, currency: Optional[str] = None) -> Config:
    env = Env()
    env.read_env(path)

    # Определите здесь вашу логику по выбору ключей для разных валют
    stripe_config = StripeConfig(
        secret_key=env('STRIPE_SECRET_KEY_USD'),
        publishable_key=env('STRIPE_PUBLISHABLE_KEY_USD')
    )

    if currency == 'EUR':
        stripe_config = StripeConfig(
            secret_key=env('STRIPE_SECRET_KEY_EUR'),
            publishable_key=env('STRIPE_PUBLISHABLE_KEY_EUR')
        )

    return Config(
        db=DatabaseConfig(
            django_secret_key=env('DJANGO_SECRET_KEY'),
        ),
        stripe=stripe_config
    )
