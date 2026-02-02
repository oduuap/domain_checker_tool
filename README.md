# 🚀 Domain Finder - Traffic Edition

Tool tìm domains có DR + Traffic từ C99.NL với WHOIS check.

## ✅ Tính Năng

- ✅ Fetch domains từ C99.NL (ru.com, sa.com, ca.com...)
- ✅ Check Traffic từ RapidAPI (Ahrefs data)
- ✅ Check WHOIS CHI TIẾT (5 trạng thái):
  - ✅ **Available** - Mua ngay
  - ⏳ **Pending Delete** - Đặt backorder (sẽ xóa trong 5 ngày)
  - ⚠️ **Redemption** - Đặt backorder (chủ cũ có 30 ngày chuộc)
  - 🔨 **Auction** - Tham gia đấu giá
  - 🔒 **Registered** - Liên hệ chủ
- ✅ Parallel checking (20 threads đồng thời)
- ✅ Real-time results
- ✅ Sort theo Traffic cao nhất
- ✅ Download Excel

## 🚀 Cài Đặt

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies (nếu chưa cài)
pip install -r requirements.txt

# 3. Chạy app
python3 app.py
```

## 💡 Sử Dụng

1. Mở: http://localhost:5000
2. Chọn TLD (ru.com, sa.com...)
3. Click "Fetch Domains từ C99.NL"
4. Click "Bắt Đầu Check Tất Cả Domains"
5. Xem real-time results
6. Download Excel

## 📊 Filter & Sort

- **Lấy domains có**: Traffic > 0 HOẶC DR > 0 HOẶC Backlinks > 0
- **Ưu tiên**: Domains CÓ traffic lên trên cùng
- **Phân loại**: 5 trạng thái WHOIS (Available/Pending/Redemption/Auction/Registered)
- **Sort**:
  1. Có traffic → Không có traffic
  2. Available → Backorder → Auction → Registered
  3. Traffic cao → thấp
  4. DR cao → thấp

## ⏱️ Thời Gian

- **Parallel mode**: 20 domains cùng lúc
- ~0.7s per domain (với WHOIS check)
- 99,076 domains ≈ **~1 giờ** (với 20 threads)
- Nhanh hơn 20x so với sequential

## 🎯 Kết Quả

- **Lấy domains có giá trị SEO**: Traffic hoặc DR hoặc Backlinks
- **Ưu tiên hiển thị**: Domains CÓ traffic lên đầu
- **Sort thứ tự**:
  1. Có traffic trước
  2. Available → Backorder → Auction → Registered
  3. Traffic/DR cao → thấp
- **Hiển thị**: Status note chi tiết + action buttons
  - Available → "🛒 Mua Ngay"
  - Pending/Redemption → "📥 Backorder"
  - Auction → "🔨 Đấu Giá"
  - Registered → "💬 Liên Hệ"

## 📈 Ví Dụ

```
Fetch: 99,076 domains từ ru.com
Check: HẾT 99,076 domains (parallel 20 threads)

Kết quả: 15,234/99,076 domains có giá trị SEO (15.4%)
  • Có traffic: 8,234 domains (8.3%)
  • Chỉ có DR/Backlinks: 7,000 domains (7.1%)

Phân loại theo status:
- ✅ Available: 2,234 domains (mua ngay)
- ⏳ Pending Delete: 67 domains (backorder)
- ⚠️ Redemption: 45 domains (backorder)
- 🔨 Auction: 23 domains (đấu giá)
- 🔒 Registered: 12,865 domains (liên hệ)

Sort: Domains có traffic hiển thị TRÊN CÙNG
```

## 🔑 API Keys

File: `app.py`
- RAPIDAPI_KEY: Lấy DR/Traffic
- C99_API_KEY: Fetch domains

**DONE!** 🎉
