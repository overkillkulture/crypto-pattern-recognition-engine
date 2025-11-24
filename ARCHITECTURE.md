# Architecture

## System Overview

The Crypto Pattern Recognition Engine is built with a modular, extensible architecture designed for high performance and scalability.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                           │
│                  (CLI, API, Web Interface)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   Pattern Recognition Engine                     │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              Core Orchestration                         │   │
│   │  - Event Loop  - Task Scheduling  - State Management   │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │              │              │              │
    ┌────▼───┐    ┌────▼───┐    ┌────▼───┐    ┌────▼───┐
    │ Data   │    │Pattern │    │  ML    │    │Analysis│
    │ Layer  │    │Detector│    │ Engine │    │ Engine │
    └────┬───┘    └────┬───┘    └────┬───┘    └────┬───┘
         │              │              │              │
    ┌────▼──────────────▼──────────────▼──────────────▼───┐
    │                Alert & Notification System           │
    └──────────────────────────────────────────────────────┘
```

## Core Components

### 1. Core Engine (`src/core/`)

**Purpose**: Central orchestration and coordination

**Key Classes**:
- `PatternRecognitionEngine`: Main engine class
- `interfaces.py`: Abstract base classes defining contracts
- `types.py`: Type definitions and data structures

**Responsibilities**:
- Component lifecycle management
- Data flow coordination
- Event handling
- State management

### 2. Data Layer (`src/data/`)

**Purpose**: Multi-exchange data ingestion and management

**Components**:
- `CryptoDataProvider`: Unified exchange interface using CCXT
- `DataCache`: Performance optimization through caching
- WebSocket handlers (Phase 6)

**Features**:
- Historical OHLCV data fetching
- Real-time data streaming
- Data normalization across exchanges
- Rate limiting and error handling

### 3. Pattern Detection (`src/patterns/`)

**Purpose**: Extensible pattern recognition framework

**Architecture**:
```
Pattern (ABC)
    ├── TechnicalPatternDetector
    │   ├── RSIPattern
    │   ├── MACDPattern
    │   ├── BollingerBandsPattern
    │   └── ... (expandable)
    │
    ├── CandlestickPatternDetector
    │   ├── DojiPattern
    │   ├── HammerPattern
    │   └── ... (100+ patterns)
    │
    ├── ChartPatternDetector
    │   ├── HeadAndShouldersPattern
    │   ├── TrianglePattern
    │   └── ... (expandable)
    │
    └── HarmonicPatternDetector
        └── ... (Phase 4)
```

**Design Principles**:
- Each pattern is a self-contained plugin
- Patterns implement the `Pattern` interface
- Easy to add new patterns without modifying core
- Confidence-based scoring system

### 4. Analysis Engine (`src/analysis/`)

**Purpose**: Comprehensive market analysis and signal generation

**Components**:
- `MarketAnalyzer`: Combines patterns into actionable insights
- Support/Resistance calculator
- Trend analyzer
- Risk assessor

**Process**:
1. Aggregate pattern results
2. Weight by confidence
3. Calculate overall market signal
4. Generate insights and recommendations

### 5. Machine Learning (`src/ml/`)

**Purpose**: Advanced pattern prediction and anomaly detection

**Planned Models** (Phase 5):
- LSTM for price prediction
- Autoencoders for anomaly detection
- Random Forest for pattern classification
- Transformer models for multi-timeframe analysis

**Features**:
- Training pipeline
- Model versioning
- A/B testing framework
- Online learning capability

### 6. Alert System (`src/alerts/`)

**Purpose**: Multi-channel notification delivery

**Supported Channels**:
- Console output
- File logging
- Webhooks (Phase 6)
- Telegram (Phase 6)
- Discord (Phase 6)
- Email (Phase 6)

**Features**:
- Priority-based filtering
- Rate limiting
- Delivery tracking
- Retry logic

### 7. API Layer (`src/api/`)

**Purpose**: External interfaces for integration

**Planned Features** (Phase 7):
- REST API (FastAPI)
- WebSocket streams
- GraphQL endpoint
- Authentication & rate limiting
- API documentation (OpenAPI/Swagger)

## Data Flow

### Pattern Detection Flow

```
1. Data Ingestion
   Exchange → CCXT → CryptoDataProvider → OHLCV

2. Pattern Detection
   OHLCV → PatternDetectors → PatternResults[]

3. Analysis
   PatternResults[] → MarketAnalyzer → AnalysisResult

4. Alert Generation
   AnalysisResult → AlertHandler → Notifications
```

### Real-time Flow (Phase 6)

```
Exchange WebSocket
    → DataProvider
    → Event Buffer
    → Pattern Detection (streaming)
    → ML Inference (real-time)
    → Alert Generation
    → WebSocket broadcast
```

## Design Patterns

### 1. Strategy Pattern
Each pattern detector implements the `Pattern` interface, allowing runtime pattern selection.

### 2. Observer Pattern
Alert handlers subscribe to pattern detection events.

### 3. Factory Pattern
Exchange connectors created based on configuration.

### 4. Plugin Architecture
Patterns are plugins that can be dynamically loaded and registered.

### 5. Pipeline Pattern
Data flows through processing stages: ingestion → detection → analysis → alerting.

## Scalability Considerations

### Horizontal Scaling
- Stateless design enables multiple engine instances
- Distributed caching (Redis) for shared state
- Message queue (RabbitMQ/Kafka) for task distribution

### Performance Optimization
- Vectorized operations using NumPy
- Async/await for I/O operations
- Caching layer to reduce API calls
- Batch processing for historical analysis

### Database Strategy
- Time-series database (InfluxDB/TimescaleDB) for OHLCV data
- Document store (MongoDB) for pattern results
- Relational DB (PostgreSQL) for configuration

## Extensibility Points

1. **New Patterns**: Implement `Pattern` interface
2. **New Exchanges**: Add CCXT configuration
3. **New Indicators**: Add to `src/utils/metrics.py`
4. **New Alert Channels**: Implement `AlertHandler` interface
5. **New ML Models**: Implement `MLModel` interface

## Security

- API keys stored in environment variables
- Secure WebSocket connections (WSS)
- API authentication (JWT)
- Rate limiting on all endpoints
- Input validation and sanitization

## Testing Strategy

- Unit tests for individual patterns
- Integration tests for end-to-end flows
- Performance benchmarks
- Backtesting framework for strategy validation

## Monitoring & Observability

- Prometheus metrics export
- Structured logging (JSON format)
- Distributed tracing (OpenTelemetry)
- Health check endpoints
- Performance profiling
