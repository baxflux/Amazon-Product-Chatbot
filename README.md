# Amazon Product Chatbot 🤖

Một hệ thống chatbot thông minh được thiết kế để cung cấp khuyến nghị sản phẩm và hỗ trợ khách hàng bằng cách sử dụng dữ liệu sản phẩm Amazon và các mô hình học máy.

## 📋 Tổng Quan Dự Án

Dự án này kết hợp **Xử Lý Ngôn Ngữ Tự Nhiên (NLP)** và **Học Máy (Machine Learning)** để tạo một chatbot hội thoại có khả năng:

- Khuyến nghị các sản phẩm Amazon chất lượng cao dựa trên truy vấn của người dùng
- Phân tích tâm trạng người dùng trong thời gian thực
- Phân loại ý định người dùng để xử lý phản hồi tốt hơn
- Cung cấp thông tin sản phẩm chi tiết và xếp hạng

## 🏗️ Kiến Trúc Dự Án

### Ngăn Xếp Công Nghệ

- **Framework Backend**: Django 5.2.8
- **Học Máy**: scikit-learn, NLTK, spaCy
- **Xử Lý Dữ Liệu**: Pandas, NumPy, pickle, joblib
- **Cơ Sở Dữ Liệu**: SQLite3
- **Thư Viện NLP**: NLTK VADER, spaCy, TF-IDF Vectorizer
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap

## 🚀 Các Tính Năng

### 1. **Khuyến Nghị Sản Phẩm Thông Minh**

- Sử dụng vectorization TF-IDF và độ tương tự cosine để tìm sản phẩm liên quan
- Lọc theo xếp hạng và tỷ lệ tâm trạng tích cực
- Hỗ trợ truy vấn tìm kiếm nâng cao (ví dụ: "tai nghe có xếp hạng > 4")

### 2. **Phân Tích Tâm Trạng Người Dùng**

- Phân loại tâm trạng trong thời gian thực (Tích Cực/Tiêu Cực/Không Xác Định)
- Sử dụng mô hình Logistic Regression được huấn luyện với TF-IDF
- Lưu trữ dữ liệu tâm trạng trong cơ sở dữ liệu để theo dõi hội thoại

### 3. **Nhận Dạng Ý Định**

- Phân loại ý định người dùng từ bộ dữ liệu hỗ trợ khách hàng Bitext
- 20+ ý định được xác định trước (ví dụ: 'đặt_hàng', 'theo_dõi_hàng', 'sự_cố_thanh_toán')
- Cung cấp các phản hồi được huấn luyện trước từ cơ sở tri thức

### 4. **Thông Tin Sản Phẩm**

- Tìm kiếm sản phẩm dựa trên ASIN với thông tin chi tiết
- Hiển thị: Tên sản phẩm, danh mục, xếp hạng trung bình, tỷ lệ tâm trạng tích cực
- Khuyến nghị sản phẩm tương tự với điểm tương tự

### 5. **Quản Lý Phiên**

- Hỗ trợ nhiều phiên cho người dùng ẩn danh
- Lưu trữ lịch sử trò chuyện trong cơ sở dữ liệu SQLite
- Theo dõi hội thoại dựa trên phiên

## 📊 Quy Trình Xử Lý Dữ Liệu

### Nguồn Dữ Liệu

1. **Bộ Dữ Liệu Đánh Giá Amazon** (1429_1.csv)

   - Chứa: ASIN, tên sản phẩm, danh mục, văn bản đánh giá, xếp hạng
   - Xử lý: Chọn 10 danh mục hàng đầu, làm sạch đánh giá

2. **Bộ Dữ Liệu Hỗ Trợ Khách Hàng Bitext** (27K phản hồi)
   - Chứa: instruction, intent, response, category
   - Xử lý: Chuẩn hóa ý định, lọc theo danh mục liên quan

### Các Bước Xử Lý (Xem: `preprocessing.ipynb`)

1. **Tải Dữ Liệu** - Đọc các tệp CSV thô
2. **Làm Sạch** - Xử lý các giá trị bị thiếu, loại bỏ bản sao
3. **Chuẩn Hóa** - Chuyển ý định thành chữ thường, chuẩn hóa định dạng
4. **Lọc** - Chọn các danh mục hàng đầu và dữ liệu chất lượng cao
5. **Trích Xuất Tính Năng** - Trích xuất từ khóa và siêu dữ liệu
6. **Kết Quả** - Lưu các bộ dữ liệu đã làm sạch để huấn luyện mô hình

## 🧠 Mô Hình Học Máy

### 1. Bộ Phân Loại Ý Định

**Tệp**: `intent_classifier.ipynb` → `model/intent_classifier.pkl`

```python
Pipeline:
TfidfVectorizer() → LogisticRegression(max_iter=1000)

Đầu vào: Văn bản hướng dẫn người dùng
Đầu ra: Ý định dự đoán (ví dụ: 'đặt_hàng', 'theo_dõi_hàng')
```

- Được huấn luyện trên 27K ví dụ hỗ trợ khách hàng
- Phân loại tin nhắn người dùng thành 20+ ý định dịch vụ
- Được sử dụng để cung cấp các phản hồi được huấn luyện trước

### 2. Bộ Phân Tích Tâm Trạng Người Dùng

**Tệp**: `sentiment.ipynb` → `model/sentiment_model_user.pkl`

```python
Pipeline:
TfidfVectorizer() → LogisticRegression()

Đầu vào: Văn bản tin nhắn người dùng
Đầu ra: Nhãn tâm trạng (Tích Cực/Tiêu Cực/Không Xác Định)
```

- Được huấn luyện trên văn bản hỗ trợ khách hàng với nhãn tâm trạng
- Sử dụng phân loại nhị phân (Tích Cực/Tiêu Cực)
- Quay lại "unknown" (không xác định) nếu mô hình không có sẵn

### 3. Công Cụ Khuyến Nghị Sản Phẩm

**Tệp**: `sentiment-review.ipynb`

**Vectorization TF-IDF + Độ Tương Tự Cosine**:

```
1. Vectorize tên/mô tả sản phẩm bằng TF-IDF
2. Tính toán ma trận tương tự trước (tfidf_matrix.pkl)
3. Để truy vấn người dùng, tính điểm tương tự
4. Xếp hạng theo độ tương tự, lọc theo xếp hạng/tâm trạng
5. Trả về các khuyến nghị hàng đầu
```

**Tiêu Chí Lọc**:

- Xếp hạng trung bình tối thiểu (nếu được chỉ định)
- Tỷ lệ tâm trạng tích cực tối thiểu (nếu được chỉ định)
- Chỉ các sản phẩm chất lượng cao (>80% tâm trạng tích cực)

### 4. Phân Tích Tâm Trạng Sản Phẩm

**Tệp**: `sentiment-review.ipynb`

```
1. Phân tích từng đánh giá bằng NLTK VADER SentimentIntensityAnalyzer
2. Tổng hợp tâm trạng theo sản phẩm (ASIN)
3. Tính tỷ lệ tích cực: (số_tích_cực / tổng_đánh_giá) * 100
4. Lọc sản phẩm có tỷ lệ tích cực >80%
5. Lưu: sentiment_summary.csv, high_quality_products.csv
```

## 🎯 Luồng Logic Chatbot

```
Đầu Vào Người Dùng
    ↓
1. Kiểm tra phản hồi Yes/No cho lời nhắc tương tự
    ↓ (Yes) → Khuyến nghị sản phẩm tương tự
    ↓ (No) → Kết thúc lời nhắc tương tự
    ↓
2. Dự đoán tâm trạng người dùng (Mô Hình Tâm Trạng)
    ↓
3. Lưu tin nhắn người dùng vào cơ sở dữ liệu
    ↓
4. Kiểm tra xem có phải là truy vấn liên quan đến sản phẩm không
    ├─ ASIN được phát hiện → Tìm kiếm thông tin sản phẩm
    │
    ├─ Từ khóa được phát hiện → Tạo khuyến nghị
    │
    └─ Cụm từ chung → Trích xuất từ khóa & khuyến nghị
    ↓
5. Nếu không liên quan đến sản phẩm, dự đoán ý định (Bộ Phân Loại Ý Định)
    ├─ Ý định khớp → Trả về phản hồi được huấn luyện trước
    └─ Không khớp → Xuyên qua
    ↓
6. Áp dụng logic hội thoại
    ├─ Chào hỏi → Tin nhắn chào mừng
    ├─ Yêu cầu trợ giúp → Hướng dẫn
    ├─ Truy vấn giá cả → Gợi ý tìm kiếm sản phẩm
    └─ Khác → Phản hồi chung chung
    ↓
7. Lưu phản hồi của bot vào cơ sở dữ liệu
    ↓
Trả về phản hồi JSON với tin nhắn & tâm trạng
```

## 📈 Tổng Quan Bộ Dữ Liệu

### Bộ Dữ Liệu Đánh Giá Amazon Đã Làm Sạch

- **Nguồn**: 1429_1.csv
- **Kích Thước**: ~48,000+ sản phẩm
- **Tính Năng**: asins, name, categories, reviews.text, reviews.rating
- **Xử Lý**: Chọn 10 danh mục hàng đầu, loại bỏ bản sao
- **Kết Quả**: `data/preprocessed-data/cleaned_amazon_reviews.csv`

### Bộ Dữ Liệu Hỗ Trợ Khách Hàng Bitext

- **Nguồn**: 27K phản hồi hỗ trợ
- **Tính Năng**: instruction, intent, response, category
- **Ý Định**: 20+ danh mục (đặt_hàng, theo_dõi_hàng, sự_cố_thanh_toán, v.v.)
- **Xử Lý**: Chuẩn hóa ý định, lọc các giá trị bị thiếu
- **Kết Quả**: `data/preprocessed-data/bitext_cleaned.csv`

### Kết Quả Phân Tích Tâm Trạng

- **Kết Quả**: `data/new-data/sentiment_summary.csv`
  - Cột: asins, positive_count, total_reviews, positive_ratio
- **Sản Phẩm Chất Lượng Cao**: `data/new-data/high_quality_products.csv`
  - Đã Lọc: positive_ratio > 80%

## 📝 Ví Dụ Sử Dụng

### Ví Dụ 1: Tìm Kiếm Sản Phẩm

```
User: "Find me headphones"
Bot: "Based on your request, here are some highly rated products:
- Sony WH-1000XM4 (Positive rating ratio: 92%, Average rating: 4.5)
- Bose QuietComfort 45 (Positive rating ratio: 88%, Average rating: 4.3)
- Apple AirPods Pro (Positive rating ratio: 95%, Average rating: 4.7)
Would you like more details?"
```

### Ví Dụ 2: Tìm Kiếm ASIN

```
User: "Tell me about B01AHB9CN2"
Bot: "Here is the information about Amazon Kindle Fire:
Positive rating ratio 87%, Average rating: 4.0.
Would you like to see similar products?"
```

### Ví Dụ 3: Tìm Kiếm Nâng Cao

```
User: "Show me laptops with rating > 4.5"
Bot: "Based on your request, here are some highly rated products:
[Filtered results with rating ≥ 4.5]"
```

### Ví Dụ 4: Hỗ Trợ Khách Hàng

```
User: "How do I place an order?"
Bot: "You can place an order by browsing products and adding them to your cart..."
(Sử dụng phản hồi được huấn luyện trước từ bộ dữ liệu Bitext)
```
