# AI Chatbot Agent for E-Commerce Application

This is a professional AI chatbot implementation using LangChain, Qwen2-7B-Instruct, and Pinecone vector database for your e-commerce platform.

## Features

- 🤖 **Advanced AI**: Powered by Qwen2-7B-Instruct via Hugging Face API
- 🔍 **RAG (Retrieval-Augmented Generation)**: Uses Pinecone vector database for product knowledge
- 💬 **Real-time Chat**: WebSocket-based chat interface
- 📊 **Product Search**: Intelligent product recommendations and search
- 📈 **Analytics**: Chat session tracking and user feedback
- 🎯 **Intent Recognition**: Understands user intents (product search, pricing, availability)
- 🔄 **Auto-sync**: Automatic product synchronization from your shop database

## Setup Instructions

### 1. API Keys Setup

Create a `.env` file in your project root with the following variables:

```bash
# Hugging Face API Token for Qwen2-7B-Instruct
HUGGINGFACE_API_TOKEN=your_huggingface_api_token_here

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=ecommerce-chatbot
```

### 2. Get API Keys

#### Hugging Face API Token:
1. Go to [Hugging Face](https://huggingface.co/)
2. Sign up/Sign in
3. Go to Settings > Access Tokens
4. Create a new token with "Read" permission
5. Copy the token to your `.env` file

#### Pinecone API Key:
1. Go to [Pinecone](https://www.pinecone.io/)
2. Sign up for a free account
3. Create a new project
4. Go to API Keys section
5. Copy your API key and environment to your `.env` file

### 3. Database Migration

Run the database migrations:

```bash
python manage.py migrate ai_chatbot_agent
```

### 4. Sync Products to Vector Database

Sync your existing products to the vector database:

```bash
python manage.py sync_products
```

Options:
- `--force`: Force resync all products
- `--batch-size 50`: Process products in batches

### 5. Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

### 6. Run the Server

```bash
python manage.py runserver
```

## Usage

### Chat Interface

Access the chatbot at: `http://localhost:8000/chatbot/`

### API Endpoints

- **Chat API**: `POST /chatbot/api/chat/`
- **Feedback**: `POST /chatbot/api/feedback/`
- **Health Check**: `GET /chatbot/api/health/`
- **Sync Products**: `POST /chatbot/api/sync-products/`

### Admin Interface

Access admin at: `http://localhost:8000/admin/`

Manage:
- Chat sessions and messages
- Product knowledge base
- Chatbot configuration
- User feedback

## API Usage Examples

### Send a Chat Message

```javascript
fetch('/chatbot/api/chat/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        message: "I'm looking for a laptop under $1000",
        session_id: "optional_session_id"
    })
})
.then(response => response.json())
.then(data => {
    console.log('Bot response:', data.response);
    console.log('Recommended products:', data.products);
});
```

### Send Feedback

```javascript
fetch('/chatbot/api/feedback/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        message_id: "message_uuid",
        feedback_type: "positive", // or "negative"
        comment: "Very helpful response!"
    })
});
```

## Customization

### System Prompt

Customize the chatbot behavior by editing the system prompt in the Django admin under "Chatbot Config".

### Product Features

Enhance product feature extraction by modifying the `_prepare_product_data` method in `sync_products.py`.

### UI Styling

Customize the chat interface by editing the CSS in `templates/ai_chatbot_agent/chat.html`.

## Monitoring and Analytics

### View Chat Statistics

Access: `http://localhost:8000/chatbot/stats/`

### Chat History

Users can view their chat history at: `http://localhost:8000/chatbot/history/`

### Health Check

Monitor system health: `http://localhost:8000/chatbot/api/health/`

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Django App     │    │   Vector DB     │
│   (HTML/JS)     │◄──►│   (LangChain)    │◄──►│   (Pinecone)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Qwen2-7B       │
                       │   (Hugging Face) │
                       └──────────────────┘
```

## Troubleshooting

### Common Issues

1. **"LLM not initialized"**: Check your Hugging Face API token
2. **"Vector store not initialized"**: Verify Pinecone API key and environment
3. **No products found**: Run `python manage.py sync_products`
4. **Import errors**: Ensure all dependencies are installed

### Debug Mode

Enable debug logging by setting `DEBUG=True` in your Django settings.

### Performance Optimization

- Use Redis for session caching
- Implement response caching for common queries
- Batch process large product catalogs
- Monitor API rate limits

## Dependencies

The following packages are automatically installed:

- `langchain` - LLM orchestration framework
- `langchain-huggingface` - Hugging Face integration
- `pinecone-client` - Vector database client
- `sentence-transformers` - Text embeddings
- `python-dotenv` - Environment variable management

## Security Considerations

- Keep API keys secure and never commit them to version control
- Use environment variables for all sensitive configuration
- Implement rate limiting for production use
- Validate and sanitize user inputs
- Use HTTPS in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs in the Django admin
3. Create an issue in the GitHub repository
4. Contact the development team

---

**Note**: This chatbot is designed for educational and development purposes. For production use, implement proper error handling, monitoring, and security measures.
