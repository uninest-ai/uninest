[] click LOGO NOT returning
[] fetch properties got proeblm, description fake(all fall back), images not showing
[] matching score too low


docker-compose exec backend python -c "
from app.services.embedding_service import get_embedding_service
import sys

print('Testing embedding service...')
try:
    service = get_embedding_service()
    print(f'✓ Embedding service created')

    # Test encoding
    embedding = service.encode_text('apartment')
    print(f'✓ Successfully encoded text, embedding shape: {len(embedding)}')
    print('SUCCESS: Embedding service works!')
except Exception as e:
    print(f'✗ ERROR: {e}')
    sys.exit(1)
"