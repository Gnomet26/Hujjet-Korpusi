
# 📚 Hújjet-Korpusı API Documentation

Bu API Django REST Framework asosida ishlab chiqilgan bo‘lib, foydalanuvchi autentifikatsiyasi, fayl yuklash va tahrirlash, admin nazorati va statistikani taqdim etadi.

**Base URL**: `https://api.saxovatuztatu.uz/api`

---

## 🔐 Authentication (User)

### 1. Register

**URL**: `/auth/register/`  
**Method**: `POST`  
**Body** *(form-data)*:
```json
{
  "username": "gnome17",
  "first_name": "Gnome",
  "last_name": "Terminal",
  "password": "12345678"
}
```

### 2. Login

**URL**: `/auth/login/`  
**Method**: `POST`  
**Headers**: none  
**Body** *(raw JSON)*:
```json
{
  "username": "azamat_jumamuratov",
  "password": "12345678"
}
```

### 3. Logout

**URL**: `/auth/logout/`  
**Method**: `POST`  
**Headers**:
```
Authorization: Token <your_token>
```

### 4. Profile

**URL**: `/auth/profile/`  
**Method**: `GET`  
**Headers**:
```
Authorization: Token <your_token>
```

---

## 📁 File Management

### 1. Upload File

**URL**: `/files/upload/`  
**Method**: `POST`  
**Headers**:
```
Authorization: Token <your_token>
```  
**Body** *(form-data)*:
```
file_path: [FAILE TANLANG]
```

### 2. My Files

**URL**: `/files/my_files/`  
**Method**: `GET`  
**Headers**:
```
Authorization: Token <your_token>
```

### 3. Download Original File

**URL**: `/files/download_base/<file_uuid>/`  
**Method**: `GET`  
**Headers**:
```
Authorization: Token <your_token>
```

### 4. Download .txt File

**URL**: `/files/download_txt/<file_uuid>/`  
**Method**: `GET`  
**Headers**:
```
Authorization: Token <your_token>
```

### 5. Get Text as String

**URL**: `/files/text/<file_uuid>/`  
**Method**: `GET`  
**Headers**:
```
Authorization: Token <your_token>
```

### 6. Update File Text

**URL**: `/files/update/`  
**Method**: `POST`  
**Headers**:
```
Authorization: Token <your_token>
```  
**Body** *(raw JSON)*:
```json
{
  "uuid": "4768d9b7-15d9-4060-90d5-ddc418375a88",
  "text": "Yangi matn"
}
```

---

## 👤 Admin API

### 1. Login

**URL**: `/admin/login/`  
**Method**: `POST`  
**Body** *(form-data)*:
```json
{
  "username": "admin_username",
  "password": "admin_password"
}
```

### 2. Users List

**URL**: `/admin/users/`  
**Method**: `GET`  
**Headers**:
```
Authorization: Token <admin_token>
```

### 3. Create New User

**URL**: `/admin/create_user/`  
**Method**: `POST`  
**Headers**:
```
Authorization: Token <admin_token>
```  
**Body** *(form-data)*:
```json
{
  "username": "new_user",
  "first_name": "Ism",
  "last_name": "Familiya",
  "password": "parol"
}
```

### 4. Delete User

**URL**: `/admin/delete_user/<username>/`  
**Method**: `DELETE`  
**Headers**:
```
Authorization: Token <admin_token>
```

---

## 📦 Admin Tasks

- **Start Merging Task**: `POST /admin/start_merge/`
- **Check Task Status**: `GET /admin/task_status/<task_id>/`
- **Download Merged Zip**: `GET /admin/download-merged/?task_id=<task_id>`

---

## 📊 Admin Statistics

**URL**: `/admin/statistika/`  
**Method**: `GET`  
**Headers**:
```
Authorization: Token <admin_token>
```

---

## 🔎 Search APIs

- **Search Files**: `GET /files/search/?file_name=query`
- **Admin Search User**: `GET /admin/search_user/?args=search_term`
- **Admin Search File**: `GET /admin/search_file/?args=search_term`

---

## ⚙️ Admin File Actions

- **Verify File**: `POST /admin/verify/<file_uuid>/<true_or_false>/`
- **Delete File**: `DELETE /admin/delete_file/<file_uuid>/`
- **Download Admin File (txt/original)**:
  - `/admin/download_admin_txt/<uuid>/`
  - `/admin/download_admin_base/<uuid>/`

---

## ℹ️ Izoh

- Barcha `Token`lar real foydalanishda foydalanuvchi avtorizatsiyasi orqali olinadi.
- Fayl ID (`uuid`) lar fayl yuklangandan so‘ng qaytarilgan javobdan olinadi.
