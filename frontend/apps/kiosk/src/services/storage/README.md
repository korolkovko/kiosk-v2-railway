# Media Storage Service

A flexible, configurable media storage abstraction for the KIOSK application that supports both local filesystem and cloud storage (S3-compatible).

## Overview

This service provides a unified interface for loading media assets (images, videos) from different storage backends:
- **Local Storage**: Load from backend HTTP endpoints serving local filesystem
- **S3 Storage**: Load from AWS S3, MinIO, DigitalOcean Spaces, Selectel, or any S3-compatible service

## Architecture

```
services/storage/
├── types/
│   ├── storageProvider.types.ts   # Interfaces and type definitions
│   └── mediaTypes.types.ts        # Media category enums
├── providers/
│   ├── localFilesystem.provider.ts # Local filesystem implementation
│   └── s3Storage.provider.ts       # S3 cloud storage implementation
├── storageFactory.ts               # Provider factory (singleton pattern)
├── storageConfig.ts                # Environment variable reader
├── index.ts                        # Public API exports
└── README.md                       # This file
```

## Configuration

### Environment Variables

Configure storage in `/frontend/apps/kiosk/.env`:

**Local Storage (Development)**:
```bash
# Choose storage provider
VITE_STORAGE_PROVIDER=local

# Backend HTTP endpoint serving local files
VITE_LOCAL_MEDIA_BASE_PATH=http://localhost:8000/media

# Path patterns for each media type (relative to base path)
VITE_LOCAL_PATH_ITEMS=/items
VITE_LOCAL_PATH_CATEGORIES_OPEN=/categories/categories_open_poster
VITE_LOCAL_PATH_CATEGORIES_SORRY=/categories/categories_sorry_poster
VITE_LOCAL_PATH_CATEGORIES_PROMOTED=/categories/categories_promoted_poster
VITE_LOCAL_PATH_SCREENSAVER=/screensaver
VITE_LOCAL_PATH_ORDER_HANDLING=/order_handling
VITE_LOCAL_PATH_FABRIC=/fabric
```

**S3 Storage (Production)**:
```bash
# Choose storage provider
VITE_STORAGE_PROVIDER=s3

# S3/CDN endpoint URL
# Examples:
# - AWS S3: https://s3.amazonaws.com
# - Selectel CDN: https://cd4e3f93-c551-4c5c-a76d-733f763920f1.selstorage.ru
# - CloudFront: https://d111111abcdef8.cloudfront.net
VITE_S3_ENDPOINT=https://cd4e3f93-c551-4c5c-a76d-733f763920f1.selstorage.ru

# Bucket name (leave empty if endpoint includes bucket, like Selectel CDN)
VITE_S3_BUCKET=

# Credentials - NOT needed for public bucket access
# Only required for:
# - Private buckets with pre-signed URLs
# - Backend media upload functionality
# - Programmatic bucket management
VITE_S3_REGION=ru-7
VITE_S3_ACCESS_KEY_ID=your-access-key-id
VITE_S3_SECRET_ACCESS_KEY=your-secret-access-key
VITE_S3_USE_SSL=true

# Path patterns for each media type (folders in bucket)
VITE_S3_PATH_ITEMS=/items
VITE_S3_PATH_CATEGORIES_OPEN=/categories_open_poster
VITE_S3_PATH_CATEGORIES_SORRY=/categories_sorry_poster
VITE_S3_PATH_CATEGORIES_PROMOTED=/categories_promoted_poster
VITE_S3_PATH_SCREENSAVER=/screensaver
VITE_S3_PATH_ORDER_HANDLING=/order_handling
VITE_S3_PATH_FABRIC=/fabric
```

### Media Types

The system organizes media into 7 categories:

| Type | Purpose | Example Files |
|------|---------|---------------|
| `ITEMS` | Food/beverage product images | `1.png`, `2.mp4` |
| `CATEGORIES_OPEN` | Category posters (items available) | `main.png`, `beverages.mp4` |
| `CATEGORIES_SORRY` | Category posters (out of stock) | `main.png`, `beverages.png` |
| `CATEGORIES_PROMOTED` | NEW/promoted category poster | `promoted.mp4` |
| `SCREENSAVER` | Idle screen backgrounds/videos | `idle_video.mp4` |
| `ORDER_HANDLING` | Thank you screens, payment UI | `thank_you.png` |
| `FABRIC` | Generic UI assets (logos, patterns) | `logo.svg` |

## Usage

### Basic Usage

```typescript
import { getStorageProvider, MediaType } from '@/services/storage'

// Get the active provider (local or S3 based on config)
const storage = getStorageProvider()

// Get full URL for a media file
const itemUrl = storage.getMediaUrl(MediaType.ITEMS, '123.png')
// Result: "http://localhost:8000/media/items/123.png" (local)
// Or: "https://cd4e3f93-c551-4c5c-a76d-733f763920f1.selstorage.ru/items/123.png" (S3)

// Get base path for a media type
const basePath = storage.getBasePath(MediaType.CATEGORIES_OPEN)
// Result: "http://localhost:8000/media/categories/categories_open_poster" (local)
```

### Advanced Usage

```typescript
import { storageConfig, getStorageProviderType, MediaType } from '@/services/storage'

// Check current provider type
const providerType = getStorageProviderType()
console.log('Using provider:', providerType) // 'local' or 's3'

// Access configuration
console.log('Config:', storageConfig)

// Check if storage is configured
import { isStorageConfigured } from '@/services/storage'
if (!isStorageConfigured()) {
  console.error('Storage not configured!')
}
```

### Using in Services

The storage provider is already integrated into:

1. **`mediaCache.service.ts`** - Downloads media from storage provider
2. **`posterLogic.service.ts`** - Builds category poster paths
3. **`getAvailableItems.mappers.ts`** - Adds item poster paths

Example from mediaCache service:

```typescript
import { getStorageProvider } from './storage/storageFactory'
import { MediaType } from './storage/types/mediaTypes.types'

// Find media file with extension detection
const storage = getStorageProvider()
const url = storage.getMediaUrl(MediaType.ITEMS, `${itemId}.png`)
const blob = await fetch(url).then(r => r.blob())
```

## Switching Storage Providers

### Local to S3 Migration

1. **Upload media to S3 bucket** matching the folder structure:
   ```bash
   # Using AWS CLI
   aws s3 sync /var/kiosk/media/ s3://mybucket/

   # Or using Selectel/other provider's web console
   ```

2. **Update `.env`**:
   ```bash
   VITE_STORAGE_PROVIDER=s3
   VITE_S3_ENDPOINT=https://your-cdn-url.com
   ```

3. **Rebuild frontend**:
   ```bash
   pnpm dev  # development
   pnpm build  # production
   ```

4. **No code changes needed!** The storage provider automatically switches.

## Storage Folder Structure

### Local Filesystem (Backend serves from `/var/kiosk/media/`)

```
/var/kiosk/media/
├── items/
│   ├── 1.png
│   ├── 2.png
│   └── 3.png
├── categories/
│   ├── categories_open_poster/
│   │   ├── main.png
│   │   └── beverages.png
│   ├── categories_sorry_poster/
│   │   ├── main.png
│   │   └── beverages.png
│   └── categories_promoted_poster/
│       └── promoted.mp4  (NEW category)
├── screensaver/
├── order_handling/
└── fabric/
```

### S3 Bucket (Flat structure without nested categories folder)

```
bucket-name/
├── items/
│   ├── 1.png
│   ├── 2.png
│   └── 3.png
├── categories_open_poster/
│   ├── main.png
│   └── beverages.png
├── categories_sorry_poster/
│   ├── main.png
│   └── beverages.png
├── categories_promoted_poster/
│   └── promoted.mp4
├── screensaver/
├── order_handling/
└── fabric/
```

**Note**: The folder structure in S3 can be different from local - just ensure the paths in `.env` match your actual structure.

## Supported S3 Providers

### AWS S3
```bash
VITE_S3_ENDPOINT=https://s3.amazonaws.com
VITE_S3_BUCKET=mybucket
```

### Selectel Cloud Storage (Russia)
```bash
# Using CDN URL (public bucket)
VITE_S3_ENDPOINT=https://cd4e3f93-c551-4c5c-a76d-733f763920f1.selstorage.ru
VITE_S3_BUCKET=  # Empty - bucket included in CDN URL
```

### DigitalOcean Spaces
```bash
VITE_S3_ENDPOINT=https://nyc3.digitaloceanspaces.com
VITE_S3_BUCKET=mybucket
```

### MinIO (Self-hosted)
```bash
VITE_S3_ENDPOINT=https://minio.yourdomain.com
VITE_S3_BUCKET=mybucket
```

## Public vs Private Buckets

### Option 1: Public Bucket (Current Setup - Recommended for Kiosks)

**Pros:**
- ✅ Simple configuration
- ✅ Fast - direct CDN access
- ✅ No authentication overhead
- ✅ Better CDN caching
- ✅ Easy debugging

**Cons:**
- ❌ Anyone with URL can access files
- ❌ No access control

**Best for:** Public kiosk menus where content is not sensitive

### Option 2: Private Bucket (Future Enhancement)

**Pros:**
- ✅ Secure - only authorized users
- ✅ Time-limited URLs
- ✅ Full access control

**Cons:**
- ❌ More complex implementation
- ❌ Requires backend URL signing
- ❌ Additional latency for signing

**Best for:** Paid content, user-specific media, compliance requirements

**To implement Option 2:**
1. Install `@aws-sdk/client-s3` and `@aws-sdk/s3-request-presigner`
2. Implement URL signing in backend or frontend
3. Use saved credentials to generate pre-signed URLs
4. Update S3 provider to use pre-signed URLs

## Supported File Formats

The system auto-detects file extensions in this order:

1. Video formats: `.mp4`, `.webm`
2. Image formats: `.png`, `.jpg`, `.jpeg`, `.gif`

## Backend Configuration (Local Mode)

When using local storage, backend serves media files via FastAPI static mount:

**`backend/.env`:**
```bash
MEDIA_PATH=/var/kiosk/media
```

**`backend/app/main.py`:**
```python
app.mount("/media", StaticFiles(directory=settings.MEDIA_PATH), name="media")
```

**CORS:** Ensure frontend origin is in `ALLOWED_ORIGINS`:
```bash
ALLOWED_ORIGINS=["http://localhost:4000"]
```

## Future Enhancements

When building the full content management system, this foundation supports:

- **Backend upload endpoints** - Admin panel for media management
- **Database URL storage** - Track media URLs in database
- **Image processing** - Resize, optimize, thumbnails
- **CDN integration** - Automatic cache invalidation
- **Media versioning** - Track changes over time
- **Private buckets** - Pre-signed URLs for secure access
- **Multi-region** - Serve media from closest region

## Troubleshooting

### Media not loading

1. **Check provider configuration**:
   ```typescript
   import { logStorageConfig } from '@/services/storage'
   logStorageConfig()
   ```

2. **Verify URLs in browser console** - Check what URLs are being fetched

3. **Test URL directly**:
   ```bash
   curl -I https://your-cdn-url.com/items/1.png
   # Should return: HTTP/2 200
   ```

### CORS errors with S3

**Symptoms:** "TypeError: Failed to fetch" in browser console

**Solution 1 - Add CORS policy to S3 bucket:**

```json
[
  {
    "AllowedOrigins": ["http://localhost:4000", "https://yourdomain.com"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag", "Content-Length", "Content-Type"],
    "MaxAgeSeconds": 3600
  }
]
```

**Solution 2 - Make bucket public (if CORS not needed):**
- Set bucket ACL to public-read
- Verify with: `curl -I <url>` (should return 200, not 403)

### 403 Forbidden errors

**Cause:** Bucket or files are not publicly accessible

**Solutions:**
1. Make bucket public in S3 console
2. Set individual file ACLs to public-read
3. Check bucket policy allows public access
4. For Selectel: Use CDN URL (`*.selstorage.ru`) instead of S3 API URL

### Wrong URL format

**Selectel specific:**
- ❌ Wrong: `https://s3.ru-7.storage.selcloud.ru/kioskzc/items/1.png` (403 Forbidden)
- ✅ Correct: `https://cd4e3f93-c551-4c5c-a76d-733f763920f1.selstorage.ru/items/1.png` (200 OK)

**Solution:** Use the CDN URL shown in Selectel console, not the S3 API endpoint

### File extension detection failing

The system tries multiple extensions automatically. Ensure files are named consistently:
- Items: `{itemId}.{ext}` (e.g., `1.png`, `2.mp4`)
- Categories: `{categoryName}.{ext}` (e.g., `main.png`, `beverages.mp4`)
- NEW category: Always `promoted.{ext}` in `categories_promoted_poster/`

### Browser caching issues

**Symptom:** Files deleted from S3 but still appear in frontend

**Solution:**
- Test in **incognito mode** to bypass cache
- Or enable **"Disable cache"** in DevTools Network tab
- Or do **hard refresh**: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows/Linux)

## Testing

### Test Local Provider
```typescript
// Set in .env: VITE_STORAGE_PROVIDER=local
import { getStorageProvider, MediaType } from '@/services/storage'

const storage = getStorageProvider()
console.log(storage.getMediaUrl(MediaType.ITEMS, '1.png'))
// Expected: "http://localhost:8000/media/items/1.png"
```

### Test S3 Provider
```typescript
// Set in .env: VITE_STORAGE_PROVIDER=s3
import { getStorageProvider, MediaType } from '@/services/storage'

const storage = getStorageProvider()
console.log(storage.getMediaUrl(MediaType.ITEMS, '1.png'))
// Expected: "https://cd4e3f93-c551-4c5c-a76d-733f763920f1.selstorage.ru/items/1.png"
```

### Test URL Accessibility
```bash
# Should return 200 OK
curl -I $(node -e "
  const { getStorageProvider, MediaType } = require('./storageFactory');
  console.log(getStorageProvider().getMediaUrl(MediaType.ITEMS, '1.png'));
")
```

## Related Files

- [mediaCache.service.ts](../mediaCache.service.ts) - IndexedDB caching with storage provider
- [posterLogic.service.ts](../posterLogic.service.ts) - Poster path logic using storage provider
- [getAvailableItems.mappers.ts](../mappers/getAvailableItems.mappers.ts) - Item poster path generation
- [backend/app/main.py](../../../../backend/app/main.py) - FastAPI media mount configuration
- [backend/app/config.py](../../../../backend/app/config.py) - Backend media path settings

## Contributing

When adding new media types:

1. **Add enum** to `mediaTypes.types.ts`:
   ```typescript
   export enum MediaType {
     // ...
     NEW_TYPE = 'new_type',
   }
   ```

2. **Update type definitions** in `storageProvider.types.ts`:
   ```typescript
   paths: {
     // ...
     [MediaType.NEW_TYPE]: string;
   }
   ```

3. **Add to config loader** in `storageConfig.ts`:
   ```typescript
   [MediaType.NEW_TYPE]: import.meta.env.VITE_LOCAL_PATH_NEW_TYPE || '/new_type'
   ```

4. **Update `.env`** files:
   ```bash
   VITE_LOCAL_PATH_NEW_TYPE=/new_type
   VITE_S3_PATH_NEW_TYPE=/new_type
   ```

5. **Update this README** with new media type documentation

6. **Create folders** in both local media path and S3 bucket
