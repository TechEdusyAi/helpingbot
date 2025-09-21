# HelpingBot Trading Platform

HelpingBot is a reference trading bot that demonstrates Clean Architecture and SOLID principles. The codebase is organised into clear layers, making it straightforward to extend or replace individual components such as strategies, market data providers and execution venues.

## Project structure

```
config/           # Configuration dataclasses and loaders
domain/           # Entities and interface contracts
application/      # Use-cases orchestrating domain logic
infrastructure/   # Adapters for external services and persistence
strategies/       # Strategy implementations (e.g. SMA crossover)
risk/             # Risk management policies
presentation/     # CLI entry-points
utils/            # Shared utilities (time, validation, backtesting)
tests/            # Unit & integration tests mirroring the layers
```

## Requirements

* Python 3.11+
* [pip](https://pip.pypa.io)

Install runtime and development dependencies:

```bash
pip install -e .[dev]
```

## Configuration

The bot loads its settings from YAML (defaults to `config.yaml`) with optional overrides provided via environment variables prefixed with `TRADING_BOT_`. Nested keys can be overridden using `__` as a separator. For example:

```bash
export TRADING_BOT_INSTRUMENTS__0=BTCUSD
export TRADING_BOT_STRATEGY__SHORT_WINDOW=10
```

A sample configuration is available in `config/example.yaml`.

## Running the bot

Execute the CLI with a configuration file and optional logging level:

```bash
python -m presentation.cli --config config/example.yaml --log-level INFO
```

To run a single iteration (useful for smoke testing or cron jobs):

```bash
python -m presentation.cli --config config/example.yaml --once
```

The CLI wires together the market data client, strategy, risk manager, order executor and persistence utilities. Components are injected via interfaces, so replacing them (e.g. plugging in a websocket feed or different strategy) only requires implementing the relevant interface and updating the wiring.

## Backtesting

A lightweight backtesting helper is available in `utils.backtesting`. Provide historical candles, a strategy, a risk manager and an order collector to simulate signal generation and trade execution.

## Testing and coverage

Run the automated test suite (unit and integration) with coverage reporting:

```bash
coverage run -m pytest
coverage report
```

The configuration enforces a minimum of 85% coverage and typical runs exceed 90%. Coverage can be inspected via `coverage html` for interactive browsing.

## Continuous integration

GitHub Actions is configured in `.github/workflows/ci.yml` to execute linting and tests on every push. It installs dependencies, runs the full pytest suite and checks coverage thresholds automatically.

## Extending the system

* **Strategies** – implement `domain.interfaces.Strategy` and drop the class into `strategies/`. Update the wiring in `presentation.cli.build_service` or create a new composition root.
* **Risk controls** – inherit from `domain.interfaces.RiskManager` to add portfolio-level checks, stop-loss rules or hedging logic without touching the application service.
* **Market data / execution** – provide adapters that implement `MarketDataProvider` or `OrderExecutor`. The application service only depends on these abstractions, so new implementations can be injected without code changes elsewhere.
* **Presentation layers** – build alternative front-ends (REST API, scheduler) by composing the same application service, maintaining the Clean Architecture boundary.

## Development workflow

1. Make changes within the appropriate layer.
2. Add or update tests alongside the affected module.
3. Run `coverage run -m pytest` to ensure the suite passes with sufficient coverage.
4. Commit changes and open a pull request – CI will run automatically.

## Logging and persistence

Infrastructure adapters provide structured logging, retry behaviour for HTTP requests and JSON-lines persistence of executions. These adapters are swappable via dependency injection, enabling straightforward integration with real exchanges, databases or message queues.

## Backtesting and utilities

Utility helpers cover validation, scheduling, time handling and basic backtesting, allowing rapid experimentation while keeping domain logic free from technical concerns.
