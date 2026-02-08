# Image Upload Feature - Before/After Photos

## Overview
Users can now attach photos to repair requests with support for "BEFORE" and "AFTER" categorization.

## Features Implemented

### 1. **Model** (`repairs/models.py`)
- New `RepairImage` model with:
  - ForeignKey to `RepairRequest`
  - Image field with file validation (JPG, PNG, GIF, WebP, max 5MB)
  - Image type choices (BEFORE/AFTER)
  - Upload timestamp and uploader tracking
  - Optional description field

### 2. **Forms** (`repairs/forms.py`)
- New `RepairImageForm` for handling image uploads
- File input validation (image files only, 5MB max)
- Image type selector (BEFORE/AFTER)
- Description field for image context

### 3. **Views** (`repairs/views.py`)
- Enhanced `create_repair_view` to process multi-file uploads
- Images are saved with their type and uploader information
- JSON parsing for image metadata

### 4. **Template - Create Repair** (`templates/repairs/create_repair.html`)
- **Drag-and-drop upload area** with visual feedback
- **Click to upload** file browser integration
- **Real-time preview** with image thumbnails
- **Before/After categorization** - toggle between BEFORE and AFTER for each image
- **Image removal** capability
- **Responsive design** with Bootstrap styling

**Key Features:**
- Supports multiple file uploads
- Drag-and-drop interface with hover effects
- Split view showing BEFORE photos on left, AFTER on right
- File size validation (5MB max)
- Image type selector overlay on hover
- Delete button for each image

### 5. **Template - Repair Detail** (`templates/repairs/repair_detail.html`)
- **Side-by-side photo display** with BEFORE/AFTER columns
- **Click to enlarge** functionality with modal
- **Image metadata display** (upload date, type badge)
- **Color-coded badges** (blue for BEFORE, green for AFTER)
- **Responsive grid layout**

**Features:**
- Grid layout for multiple photos
- Image type badges with colors
- Click to view full-size image
- Modal with close on Escape or outside click
- Upload timestamp display

### 6. **Database Configuration**
- Media directory created at `/media/`
- Settings configured:
  - `MEDIA_URL = 'media/'`
  - `MEDIA_ROOT = BASE_DIR / 'media'`
- URLs configured to serve media files in development
- Migration created: `repairs/migrations/0006_repairimage.py`

### 7. **Admin Interface** (`repairs/admin.py`)
- `RepairImage` inline in RepairRequest admin
- Separate `RepairImageAdmin` for managing images
- Displays image type, upload date, and uploader

### 8. **Styling** (`create_repair.html` & `repair_detail.html`)
- Custom CSS for upload area with hover effects
- Image preview cards with badges
- Modal for full-size image viewing
- Responsive grid layouts for different screen sizes
- Color-coded before/after sections

## Usage

### For Residents:
1. Navigate to "Create Repair Request"
2. Fill in repair details
3. Drag images into the upload area OR click to browse
4. For each image, select if it's BEFORE or AFTER
5. Click toggle button on image to change type
6. Remove unwanted images with delete button
7. Submit the form - images are uploaded with the repair request

### For Technicians/Staff:
1. View repair details
2. See BEFORE photos in left column
3. See AFTER photos in right column (initially empty)
4. Click any image to view full-size version
5. Images are organized by type with date stamps

## Technical Details

### File Upload Flow:
1. Client-side preview with FileReader API
2. Images stored with unique IDs and type
3. Form serializes image data as JSON on submit
4. Server processes with `multipart/form-data`
5. Each image saved to `media/repair_images/{filename}`

### Image Processing:
- Supported formats: JPG, JPEG, PNG, GIF, WebP
- Max file size: 5MB per image
- Multiple images allowed
- Images linked to repair request with type metadata

### Database Schema:
```
RepairImage
- id: AutoField
- repair_request: ForeignKey(RepairRequest)
- image: ImageField
- image_type: CharField(BEFORE|AFTER)
- uploaded_at: DateTimeField
- uploaded_by: ForeignKey(User)
- description: TextField (optional)
```

## Dependencies
- Pillow (for image processing)
- Django 5.2.11
- Bootstrap 5.3.2 (for UI components)

## Migration
Run the following commands:
```bash
python manage.py migrate
```

The migration `0006_repairimage` creates the RepairImage table.

## Future Enhancements
- Image rotation/editing interface
- Before/After comparison slider
- Image compression on upload
- Batch image upload for technicians
- Image annotations/markup
- Archive old images
