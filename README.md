# SKALD – Readable Font Mod (04b_03)

Mod đổi font chữ nhỏ trong **SKALD: Against the Black Priory** sang **04b_03** – chữ tròn, đều nét, dễ đọc hơn.
*English summary below.*

![So sánh trước / sau](images/compare.png)

> Ảnh trên là mô phỏng gần đúng (vẽ lại từ chính dữ liệu font của game, phóng 4×), không phải ảnh chụp trong game.

## Mod làm gì

- Thay font chữ **cỡ nhỏ** của game (mô tả, chỉ số, tên tab, nhãn nút, tooltip… – họ font `TinyFont*`) bằng 04b_03.
- Giữ **đúng cỡ chữ và nhịp dòng** của game nên giao diện không bị lệch.
- Giữ hiệu ứng **hai tông màu** của font gốc (nửa trên màu cơ bản, nửa dưới trắng) và viền khi bật *Draw Outline*.
- **Không cần cài thêm gì**: chỉ cần Windows. Mọi thứ nằm trong gói.
- Hoàn tác bất cứ lúc nào (có bản sao lưu file gốc).

**Chưa làm:** chữ **lớn** (tiêu đề kiểu gothic, nhãn Medium/Big) vẫn là font gốc. Mod không thêm tiếng Việt – game vẫn hiển thị tiếng Anh.

## Yêu cầu

- Windows 10 / 11.
- Bản game **GOG "Launch 1.0.5"** (Unity 2020.3.36). Bộ vá kiểm tra mã SHA-256 của `resources.assets`; nếu khác phiên bản đã hỗ trợ (game cập nhật, mod khác…) nó **từ chối và không sửa gì**.
- Còn trống khoảng 700 MB ở ổ cài game (để sao lưu và tạo file mới).

## Cài đặt

1. Tải gói: **Code → Download ZIP** (hoặc mục *Releases*) và giải nén ở đâu cũng được.
2. **Đóng game.**
3. Chạy **`Patch-Font.bat`** (nhấp đúp). Nếu Windows hỏi về `xdelta3.exe` (SmartScreen / diệt virus) – đó là công cụ vá mã nguồn mở, xem mục *An toàn* bên dưới.
4. Bộ vá tự tìm thư mục game. Nếu không thấy, dán đường dẫn thư mục game (thư mục chứa `SKALD Against the Black Priory.exe`).
5. Chọn **`[1]`**, đợi vài giây, rồi mở game.

Lần chạy đầu tiên tạo bản sao lưu `resources.assets.original` (khoảng 200 MB) trong `SKALD Against the Black Priory_Data`. **Đừng xoá file này** – nó dùng để hoàn tác.

Chạy không cần menu:

```bat
Patch-Font.bat -Variant 04b
Patch-Font.bat -Variant restore
Patch-Font.bat -GameDir "D:\Games\SKALD Against the Black Priory"
```

## Gỡ mod

Chạy lại `Patch-Font.bat` và chọn **`[R] Restore`**. Hoặc dùng *Verify / Repair* của GOG Galaxy.

## An toàn

- Bộ vá chỉ sửa **một file**: `SKALD Against the Black Priory_Data\resources.assets`.
- Trước khi sửa nó **kiểm tra mã SHA-256** của file gốc, **tạo sao lưu** và kiểm tra lại sau khi vá. Nếu có gì sai, nó dừng và không thay file.
- Gói **không chứa dữ liệu game**. Bản vá `patches/04b_03.xdelta` chỉ có ~19 KB, gồm pixel font mới và vài byte chỉnh sửa; nó chỉ áp dụng được lên đúng file gốc của bạn.
- `bin/xdelta3.exe` là bản dựng sẵn của [xdelta3](https://github.com/jmacd/xdelta-gpl) (mã nguồn mở, GPL). Bạn có thể thay bằng bản tự tải. File chưa được ký số nên SmartScreen có thể cảnh báo.
- Toàn bộ mã (`Patch-Font.ps1`, `src/build_patch.py`) đều đọc được, không che giấu gì.

## Câu hỏi thường gặp

**Game cập nhật rồi mod hỏng?** Chạy `Restore` *trước khi* cập nhật (hoặc dùng Verify / Repair của GOG), rồi chờ bản mod mới nếu file `resources.assets` đổi.

**Bộ vá báo "not the supported version"?** Bản game của bạn khác bản đã hỗ trợ, hoặc `resources.assets` đã bị mod khác sửa. Không có gì bị thay đổi. Mở một Issue kèm phiên bản game.

**Chữ vẫn là font cũ ở vài chỗ?** Đúng, các chỗ dùng font lớn (tiêu đề, nhãn Medium/Big) chưa được đổi.

**Sao chữ không to hơn?** Cố ý: 04b_03 có cùng cỡ với font gốc (chữ hoa cao 5 pixel) để bố cục UI không bị lệch. Cải thiện nằm ở hình dạng chữ (đều nét, phân biệt rõ `i`, `l`, `1`).

## Cách hoạt động (ngắn)

Chữ nhỏ của game vẽ từ các ảnh bitmap (atlas) chia ô vuông. Mod vẽ lại từng ký tự vào đúng ô bằng 04b_03 cỡ 8 px, tạo lại atlas viền, rồi đóng gói phần khác biệt thành bản vá nhị phân. Chi tiết ở đầu file `src/build_patch.py`. Dựng lại bản vá cần Python + UnityPy + file `04B_03__.TTF` (không đi kèm repo).

## Ghi công & giấy phép

- Font **04b_03** do **Yuji Oshimoto ("04")** thiết kế ([04.jp.org](http://www.04.jp.org/)). **Giấy phép của font chưa được xác minh bởi người làm mod** – xem [NOTICE.md](NOTICE.md). Nếu bạn là chủ sở hữu và muốn gỡ, hãy mở Issue; mod sẽ được gỡ ngay.
- Mã trong repo (`Patch-Font.ps1`, `Patch-Font.bat`, `src/`): MIT, xem [LICENSE](LICENSE).
- [xdelta3](https://github.com/jmacd/xdelta-gpl) © Joshua MacDonald, GPL.
- *SKALD: Against the Black Priory* © High North Studios. Đây là mod fan **không chính thức**, không liên kết với nhà phát triển. Dùng với rủi ro của bạn – hãy giữ bản sao lưu.

---

# English summary

A small mod that replaces SKALD's **small UI text font** (the `TinyFont*` bitmap family) with **04b_03**: rounder, evenly weighted letters that are easier to read. Same glyph height and line spacing as the original, so the UI layout does not shift. Large/medium title fonts are unchanged. English text only.

**Install (Windows, nothing else to install):** download the ZIP, close the game, run `Patch-Font.bat`, choose `[1]`. A backup `resources.assets.original` is made on first run; choose `[R]` (or run `Patch-Font.bat -Variant restore`) to undo. The patcher verifies the SHA-256 of `resources.assets` and refuses to touch anything that is not the supported build (**GOG "Launch 1.0.5"**).

**What is in the box:** `Patch-Font.bat/.ps1` (patcher), `bin/xdelta3.exe` ([xdelta3](https://github.com/jmacd/xdelta-gpl), GPL), `patches/04b_03.xdelta` (≈19 KB, contains no game data), `src/build_patch.py` (rebuild script – needs Python, UnityPy and your own copy of `04B_03__.TTF`).

**Licensing:** the 04b_03 licence has not been verified (see [NOTICE.md](NOTICE.md)); scripts are MIT. Unofficial fan mod, not affiliated with High North Studios. Use at your own risk and keep your backup.
