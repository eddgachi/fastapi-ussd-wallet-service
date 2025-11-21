# Umoja Loans API

A robust FastAPI-based backend for a micro-lending platform, featuring USSD integration via Africa's Talking, M-Pesa payment processing, and a comprehensive admin dashboard. This platform enables instant loan applications and disbursements through simple mobile dialing, making financial services accessible to both smartphone and feature phone users across Africa.

## 🌟 Key Features

### Core Lending Capabilities
- **Complete Loan Lifecycle Management**: End-to-end processing from application to repayment
- **Intelligent Credit Scoring**: Dynamic risk assessment and personalized loan limits
- **Multi-purpose Loans**: Support for emergency, business, education, and personal loans
- **Digital Wallet System**: Virtual wallet management for loan balances and transactions

### USSD Accessibility
- **Africa's Talking Integration**: Seamless USSD gateway integration for feature phone users
- **Interactive Menu System**: Multi-level USSD menus with intuitive navigation
- **Session Management**: Robust session handling with timeout protection
- **Real-time Processing**: Instant loan eligibility checks and application submission

### Payment Processing
- **M-Pesa Daraja API**: Secure integration for loan disbursements and repayments
- **STK Push & B2C Payments**: Multiple payment channel support
- **Automated Reconciliation**: Payment matching and transaction verification
- **Webhook Handling**: Real-time payment confirmation callbacks

### Performance & Security
- **Intelligent Caching**: Memcached integration for optimized read-heavy endpoints
- **Rate Limiting**: Redis-backed protection against API abuse using `slowapi`
- **Background Processing**: Celery task queue for asynchronous operations
- **Comprehensive Monitoring**: Health checks, logging, and performance metrics

### Administrative Features
- **RESTful Admin API**: Complete management of users, loans, wallets, and transactions
- **Advanced Filtering**: Pagination, search, and filtering capabilities
- **Real-time Analytics**: Loan portfolio performance and default rate tracking
- **Automated Reporting**: Financial reports and compliance documentation

## 🏗️ Technical Architecture

### Backend Stack
- **Framework**: FastAPI (Python 3.11) with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Memcached with `pymemcache` for high-performance caching
- **Rate Limiting**: Redis with `slowapi` for API protection
- **Task Queue**: Celery with Redis backend for background processing
- **Containerization**: Docker & Docker Compose
- **API Documentation**: Automatic OpenAPI/Swagger documentation

### System Architecture
```
Africa's Talking USSD → FastAPI Backend → PostgreSQL Database
         ↓                    ↓              ↓
   USSD Session Mgmt    Memcached Cache  Celery Workers
                              ↓              ↓
                        Rate Limiting   M-Pesa API | SMS Gateway
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed on your machine
- Africa's Talking account for USSD integration
- Safaricom Daraja API credentials for M-Pesa integration

### Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/eddgachi/fastapi-ussd-wallet-service
   cd fastapi-ussd-wallet-service
   ```

2. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   
   Update the following required variables in `.env`:
   ```env
   # Database
   DATABASE_URL=postgresql://umoja_user:umoja_password@db:5432/umoja_loans
   
   # Redis
   REDIS_URL=redis://redis:6379/0
   
   # Memcached
   MEMCACHED_HOST=memcached
   MEMCACHED_PORT=11211
   
   # M-Pesa Daraja API
   MPESA_CONSUMER_KEY=your_consumer_key
   MPESA_CONSUMER_SECRET=your_consumer_secret
   MPESA_PASSKEY=your_passkey
   MPESA_CALLBACK_URL=https://your-domain.com/api/v1/mpesa-callback
   
   # Africa's Talking
   AT_API_KEY=your_api_key
   AT_USERNAME=your_username
   ```

3. **Launch Services**:
   ```bash
   docker-compose up --build
   ```
   
   The API will be available at `http://localhost:8000`

4. **Run Database Migrations**:
   ```bash
   docker-compose exec web alembic upgrade head
   ```

## 📱 Africa's Talking USSD Integration

### Setup Instructions

1. **Africa's Talking Account Setup**:
   - Register at [Africa's Talking](https://africastalking.com/)
   - Navigate to the **USSD** section in your dashboard
   - Create a new USSD channel with your desired service code (e.g., `*384*89598#`)

2. **Callback URL Configuration**:
   - Set the callback URL to: `http://your-domain.com/api/v1/ussd`
   - For local development, use **ngrok** to expose your local server:
     ```bash
     ngrok http 8000
     ```
   - Use the ngrok URL: `https://your-ngrok-subdomain.ngrok.io/api/v1/ussd`

3. **Testing with Simulator**:
   - Use the [Africa's Talking Simulator](https://simulator.africastalking.com/)
   - Enter your phone number and service code
   - Expected USSD flow:
     ```
     Welcome to Umoja Loans
     1. Apply for Loan
     2. Check Loan Status
     3. Repay Loan
     4. Transaction History
     ```

### USSD User Journey

**Loan Application Flow**:
1. Dial `*384*89598#`
2. Select `1` for loan application
3. Enter desired loan amount
4. Choose loan purpose (Emergency, Business, Education, Other)
5. Receive instant application confirmation
6. Get SMS with application reference number

**Loan Repayment**:
1. Dial `*384*89598#`
2. Select `3` for loan repayment
3. Receive M-Pesa paybill instructions
4. Make payment via M-Pesa
5. Receive SMS confirmation

## 🔌 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### USSD Endpoints
- `POST /api/v1/ussd` - Handle USSD requests from Africa's Talking
- `POST /api/v1/ussd-debug` - Debug endpoint for USSD testing

#### Loan Management
- `POST /api/v1/loans` - Create new loan application
- `GET /api/v1/loans/user/{user_id}` - Get user's loan history
- `POST /api/v1/loans/{loan_id}/approve` - Approve and disburse loan
- `POST /api/v1/loans/repay` - Process loan repayment

#### Admin Endpoints
- `GET /api/v1/admin/users` - User management with pagination
- `GET /api/v1/admin/loans` - Loan portfolio management
- `GET /api/v1/admin/transactions` - Transaction history and reporting

### Rate Limiting & Caching

- **Rate Limits**: 10 requests per minute on admin endpoints
- **Caching Strategy**: 
  - Memcached with 60-second TTL for frequently accessed data
  - Cache invalidation on data updates
  - Optimized for read-heavy loan status and user profile queries

## 🔧 Development

### Running Tests
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

### Service Architecture
```yaml
services:
  web:          # FastAPI application
  celery_worker: # Background task processing
  celery_beat:   # Scheduled tasks (reminders, credit scoring)
  redis:         # Rate limiting and task queue
  memcached:     # Response caching
  db:            # PostgreSQL database
```

### Background Tasks
The system uses Celery for:
- **Loan Disbursement**: Automated M-Pesa payment processing
- **SMS Notifications**: Application status and repayment reminders
- **Credit Scoring**: Periodic credit assessment updates
- **Scheduled Operations**: Due date reminders and overdue loan management

## 🚀 Deployment

### Production Considerations
- Set `ENV=production` in environment variables
- Configure proper SSL certificates
- Set up database backups and monitoring
- Configure Africa's Talking production credentials
- Set up M-Pesa Daraja production environment

### Health Checks
- API Health: `GET /health`
- Database Connectivity: Automatic health checks in Docker
- Cache Status: Monitoring through application logs

## 📊 Monitoring & Analytics

### Key Metrics Tracked
- **Application Conversion Rate**: USSD to completed application ratio
- **Disbursement Time**: Time from application to funds receipt
- **Default Rates**: Non-performing loan percentages
- **System Performance**: Response times and error rates

### Logging
- Structured logging for all transactions
- Error tracking and alerting
- USSD session monitoring
- Payment processing audit trails

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check API documentation at `/docs`
- Review USSD integration guide in this README

---

**Umoja Loans** - Democratizing access to financial services through technology. Making instant loans accessible to everyone, everywhere.