








TÀI LIỆU KẾT NỐI API VIETTELPOST


I. Tổng quan
1.Giới thiệu chung
Hệ thống tích hợp API của Viettel Post là nền tảng kết nối hiện đại, cho phép đối tác và khách hàng dễ dàng tích hợp trực tiếp các dịch vụ logistics của Viettel Post vào hệ thống nội bộ một cách nhanh chóng, đơn giản và bảo mật.
Hệ thống cung cấp 2 môi trường độc lập phục vụ cho việc tích hợp.
Production : https://partner.viettelpost.vn
Development : https://partnerdev.viettelpost.vn

Lưu ý:
- Các request mẫu bên dưới đều để dạng Curl, có thể import trực tiếp vào Postman, thay tham số sau đó call API để lấy response mẫu.
- Trường hợp lỗi sẽ response body (application/json) có nội dung. 
- error: true
- message: Nội dung lỗi.
2. Lưu đồ tương tác hệ thống


II. Chi tiết
1.Danh mục địa danh
1.1 Danh mục địa danh (V2)
Danh mục địa danh V2 cung cấp danh mục Tỉnh/TP, Quận/Huyện và Phường/Xã theo cơ cấu hành chính cũ (trước sáp nhập). Đồng thời cũng cung cấp danh mục Tỉnh/TP và Phường/Xã theo cơ cấu hành chính mới (Sau sáp nhập)
1.1.1 Danh mục Tỉnh/TP
Mô tả
API này được sử dụng để lấy danh sách Tỉnh/ TP.
URL
https://partner.viettelpost.vn/v2/categories/listProvinceById?provinceId=-1
Phương thức
GET
Tham số yêu cầu
provinceId (bắt buộc): ID của tỉnh/thành phố muốn tra cứu. 
Có thể  truyền vào pronvinceId = -1 để lấy tất cả Tỉnh/TP
Response mẫu
{
      "PROVINCE_ID": 1,
      "PROVINCE_CODE": "HNI",
      "PROVINCE_NAME": "Hà Nội"
}
Mô tả: 
PROVINCE_ID: Mã định danh của tỉnh/thành phố trong hệ thống Viettel Post.
PROVINCE_CODE: Mã tỉnh/thành phố 
PROVINCE_NAME: Tên đầy đủ của tỉnh/thành phố.


1.1.2 Danh mục Quận/ Huyện:
Mô tả:
API này được sử dụng để lấy danh sách Quận/ Huyện theo Tỉnh/ TP.
URL 
https://partner.viettelpost.vn/v2/categories/listDistrict?provinceId=-1
Phương thức
GET
Tham số yêu cầu
provinceId (bắt buộc): ID của Tỉnh/ TP muốn tra cứu. 
Có thể  truyền vào pronvinceId = -1 để lấy tất cả Quận/ Huyện
Response mẫu
{
    "DISTRICT_ID": 325,
    "DISTRICT_VALUE": "3558",
    "DISTRICT_NAME": "HUYỆN LẠC THỦY",
    "PROVINCE_ID": 31
}
Mô tả:
DISTRICT_ID: Mã định danh của Quận/ Huyện trong hệ thống Viettel Post.
DISTRICT_NAME: Tên đầy đủ của Quận/ Huyện
PROVINCE_ID : Mã định danh của Tỉnh/ TP 




*Cập nhât API Danh mục Quận/Huyện sau sáp nhập.
Đối với 34 Tỉnh/Thành phố sau sáp nhập, trong danh sách Quận/Huyện của mỗi Tỉnh/ TP sẽ xuất hiện thêm một đối tượng có thông tin như sau:


{
"DISTRICT_ID": 100000001, // Tùy thuộc vào Tỉnh/TP
"DISTRICT_VALUE": "NEW",
“DISTRICT_NAME": "Bỏ qua - Sử dụng địa chỉ 2 cấp",
"PROVINCE_ID": 1 // Tùy thuộc vào Tỉnh/TP
}

Sử dụng DISTRICT_ID của đối tượng này khi gọi API Danh mục Phường/Xã để lấy danh sách Phường/ Xã mới (sau sáp nhập )
Ngược lại, khi sử dụng DISTRICT_ID của các Quận/ Huyện cũ khi gọi API Danh mục Phường/Xã lấy danh sách Phường/ Xã cũ (trước sáp nhập ).  
1.1.3 Danh mục Phường/ Xã:
Mô tả
API này được sử dụng để lấy danh sách Phường/ Xã theo Quận/ Huyện (áp dụng với cơ cấu hành chính cũ) và danh sách Phường/ Xã theo Tỉnh/ TP (áp dụng với cơ cấu hành chính mới)
URL 
https://partner.viettelpost.vn/v2/categories/listWards?districtId=-1
Phương thức
GET
Tham số yêu cầu
districtId (bắt buộc): ID của Quận/ Huyện muốn tra cứu. 
Có thể  truyền vào districtId = -1 để lấy tất cả ID Phường/ Xã
Response mẫu
{
  "WARDS_ID": 405,
  "WARDS_NAME": "PHƯỜNG THẠCH BÀN",
  "DISTRICT_ID": 20
}
Ý nghĩa các trường:
WARDS_ID: ID của phường/xã.
WARDS_NAME: Tên của phường/xã.
DISTRICT_ID: ID Quận/ huyện

1.2. Danh mục địa danh mới (V3) 
Danh mục địa danh mới V3 chỉ cung cấp danh sách Tỉnh/TP và Phường/Xã theo danh mục mới (Sau sáp nhập)
1.2.1 API Lấy danh sách Tỉnh/TP (v3)
Mô tả:
API này được sử dụng để lấy danh sách tất cả các tỉnh/thành phố ( danh mục địa danh mới ) .
URL (Dev)
https://partnerdev.viettelpost.vn/v3/categories/listProvinceNew
Phương thức
GET
Tham số yêu cầu
Không yêu cầu
Response mẫu
{
  "PROVINCE_ID": 1,
  "PROVINCE_CODE": "HNI",
  "PROVINCE_NAME": "Hà Nội"
}
Ý nghĩa các trường:
PROVINCE_ID: Mã định danh của tỉnh/thành phố trong hệ thống Viettel Post.
PROVINCE_CODE: Mã viết tắt của tỉnh/thành phố (ví dụ: "HNI" cho Hà Nội).
PROVINCE_NAME: Tên đầy đủ của tỉnh/thành phố.

1.2.2 API Lấy danh sách Phường/ Xã (v3)
Mô tả
API này được sử dụng để lấy danh sách các phường/xã ( danh mục địa danh mới ) theo tỉnh/thành phố
URL (Dev)
https://partnerdev.viettelpost.vn/v3/categories/listWardsNew?provinceId=1
Phương thức
GET
Tham số yêu cầu
provinceId (bắt buộc): ID của tỉnh/thành phố muốn tra cứu (ví dụ: provinceId=1). Có thể  truyền vào pronvinceId = -1 để lấy tất cả ID phường/xã
Response mẫu
{
  "WARDS_ID": 405,
  "WARDS_NAME": "PHƯỜNG THẠCH BÀN",
  "DISTRICT_ID": 20
}
Ý nghĩa các trường:
WARDS_ID: ID của phường/xã.
WARDS_NAME: Tên của phường/xã.
DISTRICT_ID: ID Quận/ huyện


2. Token
2.1 Lấy token tài khoản
Mô tả: 
Cung cấp. Token  được sử dụng để truy cập các API yêu cầu xác thực.
Ứng dụng: 
Gửi kèm token trong header khi gọi các API yêu cầu xác thực. 
Cách lấy token
 Bước 1: Đăng nhập để lấy token tạm
Request mẫu
curl --location --request POST 'https://partner.viettelpost.vn/v2/user/Login' \
--header 'Content-Type: application/json' \
--data-raw '{
    "USERNAME":"0933177454",
    "PASSWORD":"xyz@222"
}'

	Trong đó
USERNAME là tài khoản đăng ký trên https://viettelpost.vn
PASSWORD là mật khẩu của tài khoản.
Response mẫu
{
    "status": 200,
    "error": false,
    "message": "OK",
    "data": {
        "userId": 7856551,
        "token": "eyJhbGciOiJFUzI1NiJ9.eyJzdWIiOiIwMjE2NDg3ODQxMzYsIlBhcnRuZXIiOjcyMn0.vzaWimV_O16QSatsoB7yz-5oVDRBHKI8ZdJHe2Myy8N0mv1HDSgc5AeaSpfDdL97OUb6rIXQ",
        "partner": 7856551,
        "phone": "0933177454",
        "postcode": null,
        "expired": 0,
        "encrypted": null,
        "source": 5
    }
}

Trong đó: “token“ là, dữ liệu cần lấy.
 Bước 2: Lấy token dài hạn
Request mẫu
curl --location --request POST 'https://partner.viettelpost.vn/v2/user/ownerconnect' \
--header 'Token: eyJhbGciOiJFUzI1NiJ9.eyJzdWIiOiIwMjE2NDg3ODQxMzYsIlBhcnRuZXIiOjcyMn0.vzaWimV_O16QSatsoB7yz-5oVDRBHKI8ZdJHe2Myy8N0mv1HDSgc5AeaSpfDdL97OUb6rIXQ' \
--header 'Content-Type: application/json' \
--header 'Cookie: SERVERID=A' \
--data-raw '{
    "USERNAME":"0933177454",
    "PASSWORD":"xyz@222"
}'



Trong đó: Header Token = token lấy ở bước 1. Tài khoản và mật khẩu tương tự bước 1.
Response mẫu(application/json)
{
    "status": 200,
    "error": false,
    "message": "OK",
    "data": {
        "userId": 7856551,
        "token": "eyJhbGciOiJFUzI1NiJ9._K2CSZZ9BCIULb0LJdRsr0n7g",
        "partner": 7856551,
        "phone": "0933177454",
        "postcode": null,
        "expired": 0,
        "encrypted": null,
        "source": 5
    }
}


2.2 Lấy token ủy quyền truy cập
Mô tả: 
Cung cấp cơ chế truy cập ủy quyền cho các đơn vị thành viên của một đối tác, cho phép các đơn vị thành viên có thể thực hiện giao dịch trực tiếp với hệ thống của Viettel Post dưới quyền của đối tác.
Ngoài ra API này còn có thể sử dụng để lấy token dài hạn ( có thời hạn sử dụng 1-2 năm từ thời điểm lấy ).
Ứng dụng: 
Đối tác chính cung cấp token của mình lấy từ API Lấy token truy cập. Các đơn vị thành viên sử dụng token của đối tác chính gửi kèm trong header và nhập thông tin tài khoản của mình của khi gọi API Lấy token truy cập ủy quyền để lấy token truy cập ủy quyền, với token này đơn vị thành viên có thể tương tác với hệ thống của Viettelpost dưới quyền của đối tác chính
Gửi kèm token trong header khi gọi các API yêu cầu xác thực.
Request mẫu
curl --location --request POST 'https://partner.viettelpost.vn/v2/user/ownerconnect' \
--header 'Token: eyJhbGciOiJFUzI1NiJ9.eyJzdWIiOiIwMjE2NDg3ODQxMzYsIlBhcnRuZXIiOjcyMn0.vzaWimV_O16QSatsoB7yz-5oVDRBHKI8ZdJHe2Myy8N0mv1HDSgc5AeaSpfDdL97OUb6rIXQ' \
--header 'Content-Type: application/json' \
--header 'Cookie: SERVERID=A' \
--data-raw '{
    "USERNAME":"0933177454",
    "PASSWORD":"xyz@222"
}'



Trong đó: 
Header Token là token của tài khoản đối tác.
USERNAME là tài khoản
PASSWORD là mật khẩu
Tài khoản, mật khẩu đăng ký trên web https://viettelpost.vn
Response mẫu
{
    "status": 200,
    "error": false,
    "message": "OK",
    "data": {
        "userId": 7856551,
        "token": "eyJhbGciOiJFUzI1NiJ9.eyJzdWIiOiIwOTMzMTc3NDU0IiwiVXNlcklkIjo3ODU2NTUxLCJGcm9tU291cmNlIjo1LCJUb-eB-7c-5sJ2_kDcavzMImejJZXO6ZufQ_BW1r2A8yYqpT6_K2CSZZ9BCIULb0LJdRsr0n7g",
        "partner": 7856551,
        "phone": "0933177454",
        "postcode": null,
        "expired": 0,
        "encrypted": null,
        "source": 5
    }
}


Lưu token trong response để làm Header(Token) tạo đơn và tương tác với đơn hàng trong quá trình vận chuyển.
2.3 Lấy token tài khoản theo tham số bí mật ViettelPost
Bước 1. Đăng nhập vào website https://viettelpost.vn/ với tài khoản Viettel Post đã được đăng ký trước đó.
Bước 2. Truy cập vào đường dẫn https://viettelpost.vn/cau-hinh-tai-khoan hoặc thực hiện thao tác như hướng dẫn dưới đây :

2.3.1. Giao diện quản lý token

Bước 3. Click vào Thêm mới token, hộp thoại xuất hiện yêu cầu người dùng nhập Tên token mong muốn, ví dụ : Viettelpostvn. Sau đó click Xác nhận

2.3.2. Hộp thoại Thêm mới token xuất hiện
Bước 4. Sau khi tạo thành công, người dùng lựa chọn Sao chép token để có thể lấy token. Hộp thoại xuất hiện xác nhận phương thức xác thực để lấy Token (Email, SMS, Mocha).

2.3.3. Danh sách token đã được tạo


2.3.4. Hộp thoại xác thực OTP xuất hiện



2.3.5. Hộp thoại điền OTP xuất hiện

Bước 5. Người dùng điền OTP đã nhận được và nhận thông báo sao chép thành công

2.3.6. Thông báo sao chép Token thành công
Lưu token đã sao chép để làm Header(Token) khi sử dụng API Lấy token VTP.
- Request mẫu
curl --location 'https://partner.viettelpost.vn/v2/user/LoginVTP' \
--header 'Content-Type: application/json' \
--data '{
    "token":"58346742179D84F2E9"
}'



Trong đó: 
Token là token đã lấy từ website https://viettelpost.vn
- Response mẫu
{
    "status": 200,
    "error": false,
    "message": "OK",
    "data": {
        "userId": 8866484,
        "token": "eyJhbGciOiJFUzI1NiJ9.eyJzdWIiOiIwMzgyNjc4MDgwIiwiVXNlcklkIjo4ODY2NDg0LCJGcm9tU291cmNlIjo1LC",
        "partner": -1,
        "phone": "0382678080",
        "postcode": null,
        "expired": 1701461935832,
        "encrypted": null,
        "source": 5,
        "infoUpdated": true
    }
}




3. Lấy danh sách dịch vụ phù hợp với hành trình
Mô tả: 
Lấy danh sách dịch vụ chính khả dụng và dịch vụ cộng thêm đi kèm phù hợp với đối tác và địa chỉ gửi của đơn hàng.
Viettelpost cung cấp 2 API lấy danh sách dịch vụ tương ứng với 2 phương thức tạo đơn.
Lấy danh sách dịch vụ sử dụng địa chỉ chi tiết. 
Lấy danh sách dịch vụ sử dụng địa chỉ định danh. 
Ứng dụng: 
Thông tin dịch vụ chính  (MA_DV_CHINH) sẽ được truyền và tham số ORDER_SERVICE trong API tạo đơn. Dịch vụ cộng thêm (SERVICE_CODE) sẽ được truyền vào tham số ORDER_SERVICE_ADD trong API tạo đơn
Lấy danh sách dịch vụ theo ID địa danh
- Request mẫu
curl --location --request POST 'https://partner.viettelpost.vn/v2/order/getPriceAll' \
--header 'Content-Type: application/json' \
--header 'Token: 31232' \
--header 'Cookie: SERVERID=A' \
--data-raw '{
    "SENDER_DISTRICT": 12,
    "SENDER_PROVINCE": 1,
    "SENDER_WARD": 49876,
    "RECEIVER_DISTRICT": 12,
    "RECEIVER_PROVINCE": 1,
    "RECEIVER_WARD": 49876,
    "PRODUCT_TYPE": "HH",
    "PRODUCT_WEIGHT": 100,
    "PRODUCT_PRICE": 5000000,
    "MONEY_COLLECTION": "5000000",
    "PRODUCT_LENGTH": 0,
    "PRODUCT_WIDTH": 0,
    "PRODUCT_HEIGHT": 0,
    "TYPE": 1
}'


Trong đó, các trường dữ liệu được mô tả như sau
STT
Tên trường
Vị trí
Kiểu dữ liệu
Mô tả
1
Token
Header
String
Token tạo đơn của tài khoản client(Lấy ở mục 1)
2
SENDER_PROVINCE
Body
Long
ID Tỉnh gửi hàng
3
SENDER_DISTRICT
Body
Long
ID Huyện gửi hàng
4
SENDER_WARD
Body
Long
ID Phường/ Xã


5
RECEIVER_PROVINCE
Body
Long 
ID Tỉnh nhận hàng
6
RECEIVER_DISTRICT
Body
Long
ID Huyện nhận hàng
7
RECEIVER_WARD
Body
Long
ID Phường/ Xã



8
PRODUCT_TYPE
Body
String
Loại hàng hóa:
TH: Thư
HH: Hàng
9
PRODUCT_WEIGHT
Body
Long
Trọng lượng(Gr)
10
PRODUCT_PRICE
Body
Long 
Giá trị hàng(VNĐ)
11
MONEY_COLLECTION
Body
Long 
Tiền hàng cần thu hộ thu hộ(VNĐ), không bao gồm tiền cước cần thu hộ.
12
TYPE
Body
Long
Loại bảng giá
0: Bảng giá quốc tế
1: Bảng giá trong nước
13
PRODUCT_LENGTH
Body
Long
Chiều dài(cm), không bắt buộc
14
PRODUCT_WIDTH
Body
Long
Chiều rộng(cm), không bắt buộc
15
PRODUCT_HEIGHT
Body
Long
Chiều cao(cm), không bắt buộc


- Response mẫu
[
    {
        "MA_DV_CHINH": "PHS",
        "TEN_DICHVU": "Nội tỉnh tiết kiệm",
        "GIA_CUOC": 26400,
        "THOI_GIAN": "48 giờ",
        "EXCHANGE_WEIGHT": 0,
        "EXTRA_SERVICE": [
            {
                "SERVICE_CODE": "GBP",
                "SERVICE_NAME": "Báo phát",
                "DESCRIPTION": null
            },
            {
                "SERVICE_CODE": "XMG",
                "SERVICE_NAME": "Thu tiền xem hàng",
                "DESCRIPTION": null
            }
        ]
    }
]


Trong đó, các trường dữ liệu được mô tả như sau
STT
Tên trường
Vị trí
Kiểu dữ liệu
Mô tả
1
MA_DV_CHINH
Body
String
Mã dịch vụ. Dùng để gán giá trị vào trường ORDER_SERVICE trong API tạo đơn(Mục 4,5).
2
TEN_DICHVU
Body
String
Tên dịch vụ
3
GIA_CUOC
Body
Long
Tổng cước dịch vụ đã bao gồm VAT, không bao gồm phụ phí.
4
THOI_GIAN
Body
String
Thời gian cam kết giao hàng
5
EXCHANGE_WEIGHT
Body
Long
Trọng lượng quy đổi từ kích thước(gr)
6
EXTRA_SERVICE
Body
Object
Danh sách các dịch vụ cộng thêm. Trong đó
SERVICE_CODE là mã dịch vụ.
SERVICE_NAME là tên dịch vụ


Lấy danh sách dịch vụ theo địa chỉ chi tiết
- Request mẫu
curl --location --request POST 'https://partner.viettelpost.vn/v2/order/getPriceAllN
lp' \
--header 'Content-Type: application/json' \
--header 'Token: 31232' \
--header 'Cookie: SERVERID=A' \
--data-raw '
{
    "SENDER_ADDRESS": "Đại Mỗ, Nam Từ Liêm, Hà Nội",
    "RECEIVER_ADDRESS": "Định Công, Hoàng Mai, Hà Nội",
    "RECEIVER_PROVINCE": 1,
    "PRODUCT_TYPE": "HH",
    "PRODUCT_WEIGHT": 100,
    "PRODUCT_PRICE": 5000000,
    "MONEY_COLLECTION": "5000000",
    "PRODUCT_LENGTH": 0,
    "PRODUCT_WIDTH": 0,
    "PRODUCT_HEIGHT": 0,
    "TYPE": 1
}'


Trong đó, các trường dữ liệu được mô tả như sau
STT
Tên trường
Vị trí
Kiểu dữ liệu
Mô tả
1
Token
Header
String
Token (Lấy ở mục 2)
2
SENDER_ADDRESS
Body
String
Địa chỉ người gửi
4
RECEIVER_ADDRESS
Body
String 
Địa chỉ người nhận
6
PRODUCT_TYPE
Body
String
Loại hàng hóa:
TH: Thư
HH: Hàng
7
PRODUCT_WEIGHT
Body
Long
Trọng lượng(Gr)
8
PRODUCT_PRICE
Body
Long 
Giá trị hàng(VNĐ)
9
MONEY_COLLECTION
Body
Long 
Tiền hàng cần thu hộ thu hộ(VNĐ), không bao gồm tiền cước cần thu hộ.
10
TYPE
Body
Long
Loại bảng giá
0: Bảng giá quốc tế
1: Bảng giá trong nước
11
PRODUCT_LENGTH
Body
Long
Chiều dài(cm), không bắt buộc
12
PRODUCT_WIDTH
Body
Long
Chiều rộng(cm), không bắt buộc
13
PRODUCT_HEIGHT
Body
Long
Chiều cao(cm), không bắt buộc



- Response mẫu
{
    "SENDER_ADDRESS": {
        "PROVINCE_ID": 1,
        "DISTRICT_ID": 25,
        "WARD_ID": 498,
        "ADDRESS": "P.Đại Mỗ - Q.Nam Từ Liêm - TP.Hà Nội"
    },
    "RECEIVER_ADDRESS": {
        "PROVINCE_ID": 1,
        "DISTRICT_ID": 4,
        "WARD_ID": 74,
        "ADDRESS": "P.Định Công - Q.Hoàng Mai - TP.Hà Nội"
    },
    "RESULT": [
        {
            "MA_DV_CHINH": "PHS",
            "TEN_DICHVU": "Nội tỉnh tiết kiệm",
            "GIA_CUOC": 16500,
            "THOI_GIAN": "24 giờ",
            "EXCHANGE_WEIGHT": 0,
            "EXTRA_SERVICE": [
                {
                    "SERVICE_CODE": "GGD",
                    "SERVICE_NAME": "Giao Bưu phẩm tại điểm giao dịch",
                    "DESCRIPTION": null
                },
             ]
        }
    ]
}




Trong đó, các trường dữ liệu được mô tả như sau
STT
Tên trường
Vị trí
Kiểu dữ liệu
Mô tả
1
SENDER_ADDRESS
Body
Object
Địa chỉ người gửi
Trong đó
PROVINCE_ID là ID tỉnh, thành phố
DISTRICT_ID là ID quận, huyện
WARD_ID là ID phường xã
ADDRESS là địa chỉ chi tiết format theo VTP


2
RECEIVER_ADDRESS
Body
Object
Địa chỉ người nhận
Trong đó
PROVINCE_ID là ID tỉnh, thành phố
DISTRICT_ID là ID quận, huyện
WARD_ID là ID phường xã
ADDRESS là địa chỉ chi tiết format theo VTP
3
RESULT
Body
Object
Danh sách dịch vụ
4
MA_DV_CHINH
Body
String
Mã dịch vụ chính. 
Dùng để gán giá trị vào ‘ORDER_SERVICE’ trong API tạo đơn
5
TEN_DICHVU
Body
String
Tên dịch vụ
6
GIA_CUOC
Body
Long
Tổng cước dịch vụ đã bao gồm VAT, không bao gồm phụ phí.
7
THOI_GIAN
Body
String
Thời gian cam kết giao hàng
8
EXCHANGE_WEIGHT
Body
Long
Trọng lượng quy đổi từ kích thước(gr)
9
EXTRA_SERVICE
Body
Object
Danh sách các dịch vụ cộng thêm. Trong đó
SERVICE_CODE là mã dịch vụ.
SERVICE_NAME là tên dịch vụ



4. Tính cước
Mô tả: 
Tính cước dịch vụ dựa và tổng thời gian giao hàng cam kết dựa vào thông tin của đơn hàng từ đó giúp đối tác chọn ra được dịch vụ phù hợp với nhu cầu vận chuyển trước khi tạo đơn hàng.
Viettelpost cung cấp 2 API cho việc tính cước tương ứng với 2 phương thức tạo đơn.
Tính cước sử dụng địa chỉ chi tiết.
Tính cước sử dụng địa chỉ ID
  4.1 Tính cước sử dụng địa chỉ ID
- Request mẫu
curl --location --request POST 'https://partner.viettelpost.vn/v2/order/getPrice' \
--header 'Token: eyJhbGciOiJFUzI1NiJ9.9SrOP1SZVguQA7aRZJ39hIc2TbMq12HigK_Md6Yqcn-HKAgbTPwy-kRas_Oy4y7SGPDmFOdFmBxZOA' \
--header 'Content-Type: application/json' \
--data-raw '{
    "PRODUCT_WEIGHT": 100,
    "PRODUCT_PRICE": 96000,
    "MONEY_COLLECTION": 0,
    "ORDER_SERVICE_ADD": "",
    "ORDER_SERVICE": "VCBO",
    "SENDER_DISTRICT": 12,
    "SENDER_PROVINCE": 1,
    "SENDER_WARD": 49876,
    "RECEIVER_DISTRICT": 12,
    "RECEIVER_PROVINCE": 1,
    "RECEIVER_WARD": 49876,	
    "PRODUCT_LENGTH": 0,
    "PRODUCT_WIDTH": 0, 
    "PRODUCT_HEIGHT": 0,
    "PRODUCT_TYPE": "HH",
    "NATIONAL_TYPE": 1
}'


Trong đó, các trường dữ liệu được mô tả như sau
STT
Tên trường
Vị trí
Kiểu dữ liệu
Mô tả
1
Token
Header
String
Token (Lấy ở mục 2)
2
SENDER_PROVINCE
Body
Long
ID Tỉnh gửi hàng
3
SENDER_DISTRICT
Body
Long
ID Huyện gửi hàng
4
SENDER_WARD
Body
Long
ID Phường/ Xã
5
RECEIVER_PROVINCE
Body
Long 
ID Tỉnh nhận hàng
6
RECEIVER_DISTRICT
Body
Long
ID Huyện nhận hàng
7
RECEIVER_WARD
Body
Long
ID Phường/ Xã
8
PRODUCT_TYPE
Body
String
Loại hàng hóa:
TH: Thư
HH: Hàng
9
PRODUCT_WEIGHT
Body
Long
Trọng lượng(Gr)
10
PRODUCT_PRICE
Body
Long 
Giá trị hàng(VNĐ)
11
MONEY_COLLECTION
Body
Long 
Tiền hàng cần thu hộ thu hộ(VNĐ), không bao gồm tiền cước cần thu hộ.
12
NATIONAL_TYPE
Body
Long
Loại bảng giá
0: Bảng giá quốc tế
1: Bảng giá trong nước
13
PRODUCT_LENGTH
Body
Long
Chiều dài(cm), không bắt buộc
14
PRODUCT_WIDTH
Body
Long
Chiều rộng(cm), không bắt buộc
15
PRODUCT_HEIGHT
Body
Long
Chiều cao(cm), không bắt buộc
16
ORDER_SERVICE
Body
String
Mã dịch vụ
17
ORDER_SERVICE_ADD
Body
String
Mã dịch vụ cộng thêm

 
Response mẫu
{
    "status": 200,
    "error": false,
    "message": "OK",
    "data": {
        "MONEY_TOTAL_OLD": 14700,
        "MONEY_TOTAL": 14700,
        "MONEY_TOTAL_FEE": 13363,
        "MONEY_FEE": 0,
        "MONEY_COLLECTION_FEE": 0,
        "MONEY_OTHER_FEE": 0,
        "MONEY_VAS": 0,
        "MONEY_VAT": 1337,
        "KPI_HT": 48.0
    }
}


Trong đó, các trường dữ liệu được mô tả như sau
STT
Tên trường
Vị trí
Kiểu dữ liệu
Mô tả
1
MONEY_TOTAL
Body
Long
Tổng cước
2
MONEY_TOTAL_FEE
Body
Long
Cước dịch vụ chính
3
MONEY_FEE
Body
Long
Phụ phí xăng dầu
4
MONEY_COLLECTION_FEE
Body
Long
Phụ phí thu hộ
5
MONEY_OTHER_FEE
Body
Long
Phụ phí khác
6
MONEY_VAT
Body
Long
Thuế giá trị gia tăng
7
KPI_HT
Body
Double
Tổng thời gian giao hàng cam kết


4.2 Tính cước sử dụng địa chỉ chi tiết.
- Request mẫu
curl --location --request POST 'https://partner.viettelpost.vn/v2/order/getPriceNlp' \
--header 'Token: eyJhbGciOiJFUzI1NiJ9.9SrOP1SZVguQA7aRZJ39hIc2TbMq12HigK_Md6Yqcn-HKAgbTPwy-kRas_Oy4y7SGPDmFOdFmBxZOA' \
--header 'Content-Type: application/json' \
--data-raw '{
    "PRODUCT_WEIGHT": 100,
    "PRODUCT_PRICE": 96000,
    "MONEY_COLLECTION": 0,
    "ORDER_SERVICE_ADD": "",
    "ORDER_SERVICE": "VCBO",
    "SENDER_ADDRESS": "Đại Mỗ, Nam Từ Liêm, Hà Nội",
    "RECEIVER_ADDRESS": "Định Công, Hoàng Mai, Hà Nội",
    "PRODUCT_LENGTH": 0,
    "PRODUCT_WIDTH": 0,
    "PRODUCT_HEIGHT": 0,
    "PRODUCT_TYPE": "HH",
    "NATIONAL_TYPE": 1
}'


Trong đó, các trường dữ liệu được mô tả như sau
STT
Tên trường
Vị trí
Kiểu dữ liệu
Mô tả
1
Token
Header
String
Token (Lấy ở mục 2)
2
SENDER_ADDRESS
Body
String
Địa chỉ người gửi(chỉ bao gồm địa chỉ 3 cấp)
3
RECEIVER_ADDRESS
Body
Long 
Địa chỉ người nhận(chỉ bao gồm địa chỉ 3 cấp)
4
PRODUCT_TYPE
Body
String
Loại hàng hóa:
TH: Thư
HH: Hàng
5
PRODUCT_WEIGHT
Body
Long
Trọng lượng(Gr)
6
PRODUCT_PRICE
Body
Long 
Giá trị hàng(VNĐ)
7
MONEY_COLLECTION
Body
Long 
Tiền hàng cần thu hộ thu hộ(VNĐ), không bao gồm tiền cước cần thu hộ.
8
NATIONAL_TYPE
Body
Long
Loại bảng giá
0: Bảng giá quốc tế
1: Bảng giá trong nước
9
PRODUCT_LENGTH
Body
Long
Chiều dài(cm), không bắt buộc
10
PRODUCT_WIDTH
Body
Long
Chiều rộng(cm), không bắt buộc
11
PRODUCT_HEIGHT
Body
Long
Chiều cao(cm), không bắt buộc
14
ORDER_SERVICE
Body
String
Mã dịch vụ
15
ORDER_SERVICE_ADD
Body
String
Mã dịch vụ cộng thêm, không bắt buộc

 
Response mẫu
{
    "status": 200,
    "error": false,
    "message": "OK",
    "data": {
        "MONEY_TOTAL_OLD": 16500,
        "MONEY_TOTAL": 16500,
        "MONEY_TOTAL_FEE": 15278,
        "MONEY_FEE": 0,
        "MONEY_COLLECTION_FEE": 0,
        "MONEY_OTHER_FEE": 0,
        "MONEY_VAS": 0,
        "MONEY_VAT": 1222,
        "KPI_HT": 24.0,
        "EXCHANGE_WEIGHT": 0
    }
}


Trong đó, các trường dữ liệu được mô tả như sau
STT
Tên trường
Vị trí
Kiểu dữ liệu
Mô tả
1
MONEY_TOTAL
Body
Long
Tổng cước
2
MONEY_TOTAL_FEE
Body
Long
Cước dịch vụ chính
3
MONEY_FEE
Body
Long
Phụ phí xăng dầu
4
MONEY_COLLECTION_FEE
Body
Long
Phụ phí thu hộ
5
MONEY_OTHER_FEE
Body
Long
Phụ phí khác
6
MONEY_VAT
Body
Long
Thuế giá trị gia tăng
7
KPI_HT
Body
Double
Tổng thời gian giao hàng cam kết
8
EXCHANGE_WEIGHT
Body
Double
Trọng lượng quy đổi, được tính toán dựa trên kích thước 3 chiều của sản phẩm và tỉ lệ quy đổi theo hợp đồng(do nhân viên Kinh doanh của Viettelpost khai báo).



5. Tạo đơn
Mô tả: 
API này cho phép đối tác gửi yêu cầu tạo đơn hàng mới đến hệ thống Viettel Post. Khi gọi API thành công, đơn hàng sẽ được ghi nhận vào hệ thống và sẵn sàng cho các bước xử lý tiếp theo như lấy hàng và giao hàng.
Viettelpost cung cấp 2 API cho việc tạo đơn:
Tạo đơn sử dụng địa chỉ chi tiết 
Tạo đơn sử dụng địa chỉ ID
Chú thích
Địa chỉ địa chỉ chi tiết có dạng chuỗi ký tự (String).
Địa chỉ định danh có dạng mã định danh (ID) của địa chỉ. Để lấy mã định danh sử dụng API Lấy danh sách địa danh mà Viettelpost cung cấp.

5.1 Tạo đơn - Sử dụng địa chỉ chi tiết
- Request mẫu
curl --location --request POST 'https://partner.viettelpost.vn/v2/order/createOrderNlp' \
--header 'Token: eyJhbGciOiJFUzI1NiJ9.ZzZbZie_3F7_KF9RcwSc0wFFNdRIPSCULsWOcXMp6epVw' \
--header 'Content-Type: application/json' \
--header 'Cookie: SERVERID=A' \
--data-raw '{
            "ORDER_NUMBER": "BM848893946",
            "SENDER_FULLNAME": "Duong An-04",
            "SENDER_ADDRESS": "Số 18, Phường Thạnh Xuân, Quận 12,Hồ Chí Minh",
            "SENDER_PHONE": "09335656565",
            "RECEIVER_FULLNAME": "Nguyễn Văn A",
            "RECEIVER_ADDRESS": "Soso18, Phường Thạnh Xuân, Quận 12,Hồ Chí Minh",
            "RECEIVER_PHONE": "0987654321",
            "PRODUCT_NAME": "Hàng test",
            "PRODUCT_QUANTITY": 1,
            "PRODUCT_PRICE": 10000000,
            "PRODUCT_WEIGHT": 10000,
            "PRODUCT_LENGTH": 0,
            "PRODUCT_WIDTH": 0,
            "PRODUCT_HEIGHT": 0,
            "ORDER_PAYMENT": 3,
            "ORDER_SERVICE": "VCN",
            "PRODUCT_TYPE": "HH",
            "ORDER_SERVICE_ADD": null,
            "ORDER_NOTE": " Cho khách xem hàng khi nhận, cho xem hàng",
            "MONEY_COLLECTION": 56827,  
            "EXTRA_MONEY": 0,  
            "CHECK_UNIQUE": true,
            "ENABLE_SORT_CODE": true, 
            "PRODUCT_DETAIL": [
                {
                    "PRODUCT_NAME": "Hàng test",
                    "PRODUCT_QUANTITY": 1,
                    "PRODUCT_PRICE": 10000000,
                    "PRODUCT_WEIGHT": 10000
                }
            ]
        }'


Trong đó, các trường dữ liệu được mô tả như sau
STT
Tên trường
Vị trí
Kiểu dữ liệu
Bắt --buộc
Mô tả
1
Token
Header
String
X
Token (Lấy ở mục 2)
2
ORDER_NUMBER
Body
String
-
Mã đơn hàng hoặc mã quản lý nội bộ của đối tác
3
SENDER_FULLNAME
Body
String
X
Tên khách hàng gửi
4
SENDER_PHONE
Body
String
X
Số điện thoại khách hàng gửi
5
SENDER_ADDRESS
Body
String
X
Địa chỉ đầy đủ của khách hàng gửi, địa chỉ tối đa 150 byte.
6
RECEIVER_FULLNAME
Body
String
X
Tên khách hàng nhận
7
RECEIVER_PHONE
Body
String
X
Số điện thoại khách hàng nhận
8
RECEIVER_ADDRESS
Body
String
X
Địa chỉ đầy đủ của khách hàng nhận, địa chỉ tối đa 150 byte.
9
PRODUCT_NAME
Body
String
-
Tên hàng hóa
11
PRODUCT_QUANTITY
Body
Long
-
Tổng số lượng sản phẩm trong đơn hàng
Nếu không truyền mặc đinh là: 1
12
PRODUCT_PRICE
Body
Long
-
Tổng giá trị các sản phẩm trong đơn hàng
13
PRODUCT_WEIGHT
Body
Long
-
Tổng trọng lượng các sản phẩm trong đơn hàng
Nếu không truyền mặc đinh là: 50g
14
PRODUCT_LENGTH
Body
Long
-
Chiều dài(cm), không bắt buộc
15
PRODUCT_WIDTH
Body
Long
-
Chiều rộng(cm), không bắt buộc
16
PRODUCT_HEIGHT
Body
Long
-
Chiều cao(cm), không bắt buộc
17
ORDER_PAYMENT
Body
Long
X
Loại vận đơn
1. Không thu hộ
2. Thu hộ tiền hàng và tiền cước
3. Thu hộ tiền hàng, không thu hộ tiền cước.
4. Thu hộ tiền cước, không thu hộ tiền hàng.
18
ORDER_SERVICE
Body
String
X
Mã dịch vụ, lấy từ API lấy danh sách dịch vụ phù hợp hoặc tính cước.
19
ORDER_SERVICE_ADD
Body
String
-
Mã dịch vụ cộng thêm lấy từ API danh sách dịch vụ phù hợp hoặc theo hướng dẫn của nhân viên kinh doanh. Có thể chọn nhiều dịch vụ, mỗi dịch vụ cách nhau bởi dấu phẩy(,).
20
PRODUCT_TYPE
Body
String
-
Loại hàng hóa:
TH: Thư
HH: Hàng hóa
Nếu không truyền mặc đinh là: HH
21
ORDER_NOTE
Body
String
-
Ghi chú (Cho xem hàng, thời gian giao, …).
Tối đa 150 byte.
22
MONEY_COLLECTION
Body
Long
-
Tiền hàng cần thu hộ
23
PRODUCT_DETAIL
Body
List< Object>
-
Danh sách hàng hóa chi tiết(Chỉ dùng để đối soát khi có thất thoát).
Danh sách các Object có các thuộc tính như sau:
PRODUCT_NAME: tên sản phẩm, String. 
PRODUCT_QUANTITY: Số lượng, Long.
PRODUCT_PRICE: Giá trị, Long.
PRODUCT_WEIGHT: Trọng lượng, Long.
24
CHECK_UNIQUE
Body
Boolean


Không bắt buộc, giá trị = true/false tương đương với yêu cầu kiểm trùng mã đơn hàng hoặc không.
25
EXTRA_MONEY
Body
Long
-
Tiền thu khi cho khách xem hàng nhưng không lấy, không vượt quá 2 lần tổng cước. Trường dữ liệu này chỉ có ý nghĩa khi có sử dụng dịch vụ cộng thêm XMG(Xem hàng thu tiền).
26
RETURN_ADDRESS
Body
Object
-
Thông tin địa chỉ hoàn hàng. Dạng json Object có các thuộc tính như sau:
- REQUIRED: Xác nhận hoàn theo địa chỉ này, kiểu Boolean(true/false).
- FULLADDRESS: Địa chỉ hoàn đầy đủ, kiểu String.
- PROVINCE_ID: ID Tỉnh hoàn về, kiểu Long.
- DISTRICT_ID: ID quận/Huyện hoàn về, kiểu Long.
- WARDS_ID: ID Phường/xã hoàn về, kiểu Long.
27
ENABLE_SORT_CODE
Body
String
-
Mã chia chọn của VTP. 
Gồm 2 giá trị:
- true: Lấy mã sort_code, kết quả được trả về ở response
- false : Không lấy mã sort_code 

Lưu ý: Các đối tác sử dụng nhãn in riêng cần  hiển thị sort_code trên nhãn in.



28
VERIFICATION_CODE
Body
Object
-
Đối tượng chứa thông tin xác thực người nhận. Tùy chọn sử dụng khi muốn xác thực trực tiếp thay vì OTP

- TYPE: Loại xác thực. Giá trị hợp lệ: "birth_year" (năm sinh), "id_card_suffix" (6 số cuối CCCD)

- VALUE: Giá trị xác thực tương ứng với type. Nếu type="birth_year": 4 số (YYYY). Nếu type="id_card_suffix": 6 số

Lưu ý: Chỉ truyền tham số‘VERIFICATION_CODE’ khi sử dụng dịch vụ cộng thêm (ORDER_SERVICE_ADD): 'PTTX'.

Lưu ý: Riêng với các trường String, maxlength mặc định = 150 bytes

Response mẫu
{
    "status": 200,
    "error": false,
    "message": "OK",
    "data": {
        "ORDER_NUMBER": "15878180012",
        "MONEY_COLLECTION": 562000,
        "EXCHANGE_WEIGHT": 50,
        "MONEY_TOTAL": 16500,
        "MONEY_TOTAL_FEE": 15000,
        "MONEY_FEE": 0,
        "MONEY_COLLECTION_FEE": 0,
        "MONEY_OTHER_FEE": 0,
        "MONEY_VAS": 0,
        "MONEY_VAT": 1500,
        "KPI_HT": 48.0,
        "RECEIVER_PROVINCE": 34,
        "RECEIVER_DISTRICT": 390,
        "RECEIVER_WARD": 7393
    }
}


Trong đó, các trường dữ liệu được mô tả như sau
STT
Tên trường
Vị trí
Kiểu dữ liệu
Mô tả
1
ORDER_NUMBER
Body
String
Mã vận đơn (Do Viettelpost tự sinh)
2
MONEY_COLLECTION
Body
Long
Tổng tiền thu hộ
3
MONEY_TOTAL
Body
Long
Tổng cước phí
4
MONEY_TOTAL_FEE
Body
Long
Phí vận chuyển
5
MONEY_FEE
Body
Long
Phí xăng dầu
6
MONEY_COLLECTION_FEE
Body
Long
Phí thu hộ
7
MONEY_VAT
Body
Long
Thuế giá trị gia tăng
8
KPI_HT
Body
Double
Thời gian giao hàng cam kết(Tính từ 24 giờ ngày nhận được đơn hàng).
9
EXCHANGE_WEIGHT
Body
Long
Trọng lượng quy đổi
10
RECEIVER_PROVINCE
Body
Long
ID Tỉnh nhận
11
RECEIVER_DISTRICT
Body
Long
ID Huyện nhận
12
RECEIVER_WARD
Body
Long
ID Phường nhận


5.2 Tạo đơn - Sử dụng địa chỉ ID
- Url: https://partner.viettelpost.vn/v2/order/createOrder
- Method: POST, header Token
- Body
{
  "ORDER_NUMBER" : "12",
  "GROUPADDRESS_ID" : 5818802,
  "CUS_ID" : 722,
  "DELIVERY_DATE" : "11/10/2018 15:09:52",
  "SENDER_FULLNAME" : "Yanme Shop",
  "SENDER_ADDRESS" : "Số 5A ngách 22 ngõ 282 Kim Giang, Đại Kim, Hoàng Mai, Hà Nội",
  "SENDER_PHONE" : "0967.363.789",
  "SENDER_EMAIL" : "vanchinh.libra@gmail.com",
  "SENDER_WARD" : 25,
  "SENDER_DISTRICT" : 4,
  "SENDER_PROVINCE" : 1,
  "SENDER_LATITUDE" : 0,
  "SENDER_LONGITUDE" : 0,
  "RECEIVER_FULLNAME" : "Hoàng - Test",
  "RECEIVER_ADDRESS" : "1 NKKN P.Nguyễn Thái Bình, Quận 1, TP Hồ Chí Minh",
  "RECEIVER_PHONE" : "0907882792",
  "RECEIVER_EMAIL" : "hoangnh50@fpt.com.vn",
  "RECEIVER_WARD" : 25,
  "RECEIVER_DISTRICT" : 43,
  "RECEIVER_PROVINCE" : 2,
  "RECEIVER_LATITUDE" : 0,
  "RECEIVER_LONGITUDE" : 0,
  "PRODUCT_NAME" : "Máy xay sinh tố Philips HR2118 2.0L ",
  "PRODUCT_QUANTITY" : 1,
  "PRODUCT_PRICE" : 2292764,
  "PRODUCT_WEIGHT" : 40000,
  "PRODUCT_LENGTH" : 38,
  "PRODUCT_WIDTH" : 24,
  "PRODUCT_HEIGHT" : 25,
  "PRODUCT_TYPE" : "HH",
  "ORDER_PAYMENT" : 3,
  "ORDER_SERVICE" : "VCN",
  "ORDER_SERVICE_ADD" : "",
  "ORDER_VOUCHER" : "",
  "ORDER_NOTE" : "cho xem hàng, không cho thử",
  "MONEY_COLLECTION" : 2292764,
  "EXTRA_MONEY" : 0,
  "CHECK_UNIQUE" : true,
  "ENABLE_SORT_CODE" : true,
  "LIST_ITEM" : [
    {
      "PRODUCT_NAME" : "Máy xay sinh tố Philips HR2118 2.0L ",
      "PRODUCT_PRICE" : 2150000,
      "PRODUCT_WEIGHT" : 2500,
      "PRODUCT_QUANTITY" : 1
    }
  ]
}



Trong đó, các trường dữ liệu được mô tả như sau
STT
Tên trường
Vị trí
Kiểu dữ liệu
Bắt buộc
Mô tả
1
Token
Header
String
X
Token (Lấy ở mục 2)
2
ORDER_NUMBER
Body
String
-
Mã đơn hàng hoặc mã quản lý nội bộ của đối tác
3
SENDER_FULLNAME
Body
String
X
Tên khách hàng gửi
4
SENDER_PHONE
Body
String
X
Số điện thoại khách hàng gửi
5
SENDER_ADDRESS
Body
String
X
Địa chỉ đầy đủ của khách hàng gửi, địa chỉ tối đa 150 byte.
6
SENDER_PROVINCE
Body
Long
X
ID Tỉnh gửi.
7
SENDER_DISTRICT
Body
Long
X
ID Huyện gửi
8
SENDER_WARD
Body
Long
X
ID Phường xã gửi hàng
9
RECEIVER_FULLNAME
Body
String
X
Tên khách hàng nhận
10
RECEIVER_PHONE
Body
String
X
Số điện thoại khách hàng nhận
11
RECEIVER_ADDRESS
Body
String
X
Địa chỉ đầy đủ của khách hàng nhận, địa chỉ tối đa 150 byte.
12
RECEIVER_PROVINCE
Body
Long
X
ID Tỉnh nhận hàng
13
RECEIVER_DISTRICT
Body
Long
X
ID Huyện nhận hàng
14
RECEIVER_WARD
Body
Long
X
ID Phường xã nhận hàng
15
PRODUCT_NAME
Body
String


Tên hàng hóa
17
PRODUCT_QUANTITY
Body
Long
-
Tổng số lượng sản phẩm trong đơn hàng
Nếu không truyền mặc đinh là: 1
18
PRODUCT_PRICE
Body
Long
-
Tổng giá trị các sản phẩm trong đơn hàng
19
PRODUCT_WEIGHT
Body
Long
-
Tổng trọng lượng các sản phẩm trong đơn hàng
Nếu không truyền mặc đinh là: 50g
20
PRODUCT_LENGTH
Body
Long
-
Chiều dài(cm), không bắt buộc
21
PRODUCT_WIDTH
Body
Long
-
Chiều rộng(cm), không bắt buộc
22
PRODUCT_HEIGHT
Body
Long
-
Chiều cao(cm), không bắt buộc
23
ORDER_PAYMENT
Body
Long
X
Loại vận đơn
1. Không thu hộ
2. Thu hộ tiền hàng và tiền cước
3. Thu hộ tiền hàng
4. Thu hộ tiền cước
24
ORDER_SERVICE
Body
String
X
Mã dịch vụ, lấy từ API lấy danh sách dịch vụ phù hợp 
25
ORDER_SERVICE_ADD
Body
String
-
Mã dịch vụ cộng thêm lấy từ API danh sách dịch vụ phù hợp hoặc theo thông báo của nhân viên kinh doanh.
26
PRODUCT_TYPE
Body
String
-
Loại hàng hóa:
TH: Thư
HH: Hàng hóa
Nếu không truyền mặc đinh là: HH
27
ORDER_NOTE
Body
String
-
Ghi chú (Cho xem hàng, thời gian giao, …).
Tối đa 150 byte.
28
MONEY_COLLECTION
Body
Long
-
Tiền hàng cần thu hộ
29
LIST_ITEM
Body
List<Object>
-
Danh sách hàng hóa chi tiết(Chỉ dùng để đối soát khi có thất thoát).
List gồm các Object json có tham số như sau:
PRODUCT_NAME: tên sản phẩm, kiểu String
PRODUCT_QUANTITY: Số lượng, kiểu Long.
PRODUCT_PRICE: Giá trị, kiểu Long.
PRODUCT_WEIGHT: Trọng lượng(gr), kiểu Long.
30
RETURN_ADDRESS
Body
Object
-
Thông tin địa chỉ hoàn hàng, trong trường hợp địa chỉ hoàn vè là một địa chỉ khác điểm gửi hàng. 
Dạng json Object có các thuộc tính như sau:
- REQUIRED: Xác nhận hoàn theo địa chỉ này, kiểu Boolean(true/false).
- FULLADDRESS: Địa chỉ hoàn đầy đủ, kiểu String.
- PROVINCE_ID: ID Tỉnh hoàn về, kiểu Long.
- DISTRICT_ID: ID quận/Huyện hoàn về, kiểu Long.
- WARDS_ID: ID Phường/xã hoàn về, kiểu Long.
31
GROUPADDRESS_ID
Body
Long
-
Để = 0
32
CHECK_UNIQUE
Body
Boolean(true/False)
-
Không bắt buộc. Sử dụng để check trùng Mã đơn hàng.
33
EXTRA_MONEY
Body
Long
-
Tiền thu khi cho khách xem hàng nhưng không lấy, không vượt quá 2 lần tổng cước. Trường dữ liệu này chỉ có ý nghĩa khi có sử dụng dịch vụ cộng thêm XMG(Xem hàng thu tiền).
34
ENABLE_SORT_COD






Lấy thông tin mã chia chọn của VTP
- true: có lấy mã sort_code được trả về ở response
- false : Không lấy mã sort_code 


35
VERIFICATION_CODE
Body
Object
-
Đối tượng chứa thông tin xác thực người nhận. Tùy chọn sử dụng khi muốn xác thực trực tiếp thay vì OTP

- TYPE: Loại xác thực. Giá trị hợp lệ: "birth_year" (năm sinh), "id_card_suffix" (6 số cuối CCCD)

- VALUE: Giá trị xác thực tương ứng với type. Nếu type="birth_year": 4 số (YYYY). Nếu type="id_card_suffix": 6 số

Lưu ý: Chỉ truyền ‘Verification_code’ khi sử dụng dịch vụ cộng thêm (ORDER_SERVICE_ADD): 'PTTX'.

 Lưu ý: Riêng đối với các trường dữ liệu kiểu String, maxlength mặc định là 150 bytes.

Response: Giống với request Tạo đơn(4).
6. Cập nhật thông tin đơn hàng
Url: 
https://partner.viettelpost.vn/v2/order/edit    
Method: 
POST
- Curl mẫu:
curl --location 'https://partnerdev.viettelpost.vn/v2/order/edit' \
--header 'Token: eyJhbGciOiJFUzI1NiJ9.eyJzdWIiOiIwMzM4MDgyODExIiwiVXNlcklkIjo3NjU3MTQ5LCJGcm9tU291cmNlIjo1LCJUb2tlbiI6IkpZSFIwMFo1QzQiLCJleHAiOjE4MTIzMzQwNDgsIlBhcnRuZXIiOjc2NTcxNDl9.zwcI6uQdf4ly1yWaeR_q0s9pNesDg1BxdpyP09PjceYTWwY6xLBgfHh2zbxexsCMZ4Lxf1jg7ZYQoe4fbx6OpA' \
--header 'Content-Type: application/json' \
--data-raw '{
    "ORDER_NUMBER": "28936127423",
    "GROUPADDRESS_ID": "",
    "CUS_ID": "",
    "DELIVERY_DATE": "26/06/2024 15:09:52",
    "SENDER_FULLNAME": "NGUYEN VAN A",
    "SENDER_ADDRESS": "SỐ 15 DUY TÂN, DỊCH VỌNG HẬU, CẦU GIẤY, HÀ NỘI",
    "SENDER_PHONE": "0338082811",
    "SENDER_EMAIL": "nguyenvana@gmail.com",
    "RECEIVER_FULLNAME": "Linh Nguyen",
    "RECEIVER_ADDRESS": "SỐ 1 Ô CHỢ DỪA, ĐỐNG ĐA, HÀ NỘI",
    "RECEIVER_PHONE": "0338082811",
    "RECEIVER_EMAIL": "linhlinh@mail.com.vn",
    "PRODUCT_NAME": "Máy xay sinh tố Philips HR2118 2.0L",
    "PRODUCT_QUANTITY": 1,
    "PRODUCT_PRICE": 0,
    "PRODUCT_WEIGHT": 500,
    "PRODUCT_LENGTH": 38,
    "PRODUCT_WIDTH": 24,
    "PRODUCT_HEIGHT": 25,
    "PRODUCT_TYPE": "HH",
    "ORDER_PAYMENT": 3,
    "ORDER_SERVICE": "VCN",
    "ORDER_SERVICE_ADD": "",
    "ORDER_VOUCHER": "",
    "ORDER_NOTE": "Không cho xem hàng",
    "MONEY_COLLECTION": 21500,
    "EXTRA_MONEY”: 0,
    "CHECK_UNIQUE": true,
    "LIST_ITEM": [
        {
            "PRODUCT_NAME": "Tên hàng hóa 1",
            "PRODUCT_PRICE": 210000,
            "PRODUCT_WEIGHT": 250,
            "PRODUCT_QUANTITY": 1
        }
}'


- Request và response giống với API tạo đơn (5), tuy nhiên đơn hàng chỉ được sửa khi trạng thái(ORDER_STATUS) < 200.


7. Webhook
7.1 Thông tin chung
Webhook là một cơ chế callback do hệ thống Viettel Post cung cấp, cho phép gửi dữ liệu tự động đến URL do đối tác cấu hình trước. Mỗi khi đơn hàng có sự thay đổi trạng thái (ví dụ: đã lấy hàng, đang giao, giao thành công, thất bại, hoàn hàng…), hệ thống sẽ gửi một HTTP POST request chứa thông tin cập nhật về đơn hàng đến endpoint Webhook của đối tác.
Flow webhook của Viettelpost:


Lưu ý:
Mỗi tài khoản chỉ có thể cấu hình 1 webhook endpoint (URL) dùng để nhận dữ liệu hành trình đơn hàng. 
Khi sử dụng cơ chế ủy quyền, dữ liệu hành trình đơn hàng sẽ được gửi về webhook endpoint (URL) của tài khoản ủy quyền vì vậy tài khoản được ủy quyền (client) không cần cấu hình webhook.
Cần trả lại trạng thái HTTP status 200 với các trường hợp thành công, ngược lại trả lại HTTP status khác 200 với các trường hợp lỗi. Hệ thống của VTP sẽ thực hiện retry 5 lần, nếu sau 5 lần không thành công thì vui lòng lưu lại thông tin mã vận đơn và báo với đội kỹ thuật VTP xử lý manual các trường hợp này.
Hành trình có thể bị trùng hoặc thừa (do nghiệp vụ, logic xử lý trên hệ thống core của Viettelpost). Cần trả lại trạng thái (HTTP status) 200 để bypass các trường hợp này. 
Khi đơn hàng có trạng thái cuối (Trạng thái 101/107/201/501/503/504) nó sẽ không phát sinh thêm bất cứ trạng thái nào nữa, đồng nghĩa với việc dừng cập nhật hành trình 

Webhook trả về link ảnh gạch báo phát. Ảnh có định dạng .jpg và có thời hạn lưu trữ là 6 tháng. Trong các gói Webhook cơ bản chưa thiết lập mặc định trả về link ảnh báo phát, vì thế đối tác nếu muốn nhận link ảnh qua webhook cần báo lại với Viettel Post.
Link ảnh ở môi trường Development
Link ảnh ở môi trường Production
s3user10106.s3.cloudstorage.com.vn
cloudstorage.com.vn




 Request webhook mẫu
Method: POST
Header: Authorization >> Authorization là  giá trị được cấu hình tại tham số Secret parameters trang cấu hình webhook.
Format: Raw, application/json
Dữ liệu
{
"DATA": {
"ORDER_NUMBER": "TUANPAD3024822076",
"ORDER_REFERENCE": "TUANPAD3024822076",
"ORDER_STATUSDATE": "10/11/2025 11:07:16",
"ORDER_STATUS": 104,
"STATUS_NAME": "Giao cho Bưu tá đi nhận",
"LOCALION_CURRENTLY": "HNI, GLM, Bưu cục Gia Lâm - HNI - Hà Nội, 0334128111, 131003, THỊ TRẤN TRÂU QUỲ",
"NOTE": "Phân công bưu tá nhận hàng",
"MONEY_COLLECTION": 0,
"MONEY_FEECOD": 1000,
"MONEY_TOTALFEE": 236115,
"MONEY_TOTAL": 266884,
"MONEY_TOTALVAT": 19769,
"EXPECTED_DELIVERY": "Dịch vụ chưa quy định chỉ tiêu",
"PRODUCT_WEIGHT": 7100,
"ORDER_SERVICE": "VHT",
"ORDER_SERVICE_ADD": null,
"ORDER_PAYMENT": 1,
"EXPECTED_DELIVERY_DATE": null,
"DETAIL": [],
"VOUCHER_VALUE": 0,
"MONEY_COLLECTION_ORIGIN": null,
"EMPLOYEE_NAME": "Phạm Minh Đức",
"EMPLOYEE_PHONE": "84967299927",
"IS_RETURNING": false,
"POD": {
"IMAGES": []
},
"REASON_CODE": null,
"RECEIVER_FULLNAME": "Nguyễn Cường",
"LOCATION_CURRENTLY": "HNI, GLM, Bưu cục Gia Lâm - HNI - Hà Nội, 0334128111, 131003, THỊ TRẤN TRÂU QUỲ"

},
"TOKEN": "0333333333"
}




Trong đó, các trường dữ liệu được mô tả như sau
Tên Trường
Loại dữ liệu
Mô tả
Giá trị Mẫu
DATA
Object
Chứa toàn bộ dữ liệu chi tiết của đơn hàng và trạng thái.




ORDER_NUMBER
String
Mã vận đơn được tạo bởi VTP.
TUANPAD3024822076


ORDER_REFERENCE
String
Mã tham chiếu đơn hàng (thường là mã đơn hàng của Đối tác gửi lên).
TUANPAD3024822076


ORDER_STATUSDATE
DateTime String
Thời điểm thực tế trạng thái đơn hàng được cập nhật.
10/11/2025 11:07:16


ORDER_STATUS
Integer
Mã trạng thái đơn hàng (*Mã code nội bộ của VTP).
104


STATUS_NAME
String
Tên mô tả của trạng thái đơn hàng theo mã STATUS.
Giao cho Bưu tá đi nhận


LOCALION_CURRENTLY
String
Vị trí hiện tại của bưu gửi. Bao gồm các thông tin về Bưu cục/Địa danh.
HNI, GLM, Bưu cục...


NOTE
String
Ghi chú chi tiết về hành động (hay trạng thái) vừa thực hiện.
Phân công bưu tá nhận hàng


MONEY_COLLECTION
Number
Số tiền thu hộ (COD) khách hàng phải trả khi nhận hàng.
0


MONEY_FEECOD
Number
Phí thu hộ (COD) đã tính.
1000


MONEY_TOTALFEE
Number
Phí vận chuyển (chưa bao gồm VAT và các phụ phí).
236115


MONEY_TOTAL
Number
Tổng phí vận chuyển (báo gồm VAT và các phụ phí)
266884


MONEY_TOTALVAT
Number
VAT 
19769


EXPECTED_DELIVERY
String
Chỉ tiêu thời gian giao hàng dự kiến.
Dịch vụ chưa quy định chỉ tiêu


PRODUCT_WEIGHT
Number
Trọng lượng sản phẩm (gram).
7100


ORDER_SERVICE
String
Mã dịch vụ vận chuyển được sử dụng 
VHT


ORDER_SERVICE_ADD
String
Mã dịch vụ cộng thêm được sử dụng 
null


ORDER_PAYMENT
Integer
Hình thức thanh toán cước phí 
1


EXPECTED_DELIVERY_DATE
DateTime String
Ngày giao hàng dự kiến 
null


DETAIL
Array (Object)
Chi tiết các sự kiện/hành trình nhỏ trong trạng thái này 




VOUCHER_VALUE
String
Giá trị Voucher đã được áp dụng.
0


MONEY_COLLECTION_ORIGIN
Number
Giá trị tiền thu hộ ban đầu (trước khi điều chỉnh).
Lưu ý: MONEY_COLLECTION_ORIGIN ở thời điểm trước TT200 (Nhập doanh thu) luôn có giá trị null => Không dùng giá trị này.


null


EMPLOYEE_NAME
String
Tên nhân viên bưu tá/người phụ trách đang xử lý bưu gửi.
Phạm Minh Đức


EMPLOYEE_PHONE
String
Số điện thoại của nhân viên phụ trách.
84967299927


IS_RETURNING
Boolean
Trạng thái: true nếu đơn hàng đang trong quá trình chuyển hoàn/trả hàng, false nếu đang trong quá trình giao hàng 
false


POD
Object
Chi tiết Proof of Delivery (Bằng chứng giao hàng), chứa mảng các hình ảnh liên quan.
{"IMAGES":[]}


REASON_CODE
String
Mã lý do nếu đơn hàng.
null


RECEIVER_FULLNAME
String
Tên đầy đủ của người nhận.
Nguyễn Cường


LOCATION_CURRENTLY
String
Thông tin vị trí hiện tại của đơn hàng.
HNI, GLM, Bưu cục Gia Lâm...


ORDER_NOTE
String
Ghi chú của đơn hàng
Giao trong giờ hành chính


GROUPADDRESS_ID
String
Mã kho của đơn hàng
5818802
TOKEN
String
Mã Token bảo mật (Secret Key) do đối tác cung cấp cho VTP, dùng để Đối tác xác thực nguồn gốc của Webhook (đảm bảo tính toàn vẹn và bảo mật).




7.2 Hướng dẫn tích hợp webhook
B1: Truy cập hệ thống partner 
Production : https://partner.viettelpost.vn
Development: https://partnerdev.viettelpost.vn
B2: Thực hiện cấu hình webhook tại mục Cấu hình tài khoản (Account configuration)
>> Thông tin nhận hành trình (Information to receive journey)
B3: Hoàn thành Checklist Go-live (mục 9.3). 
Lưu ý: 
Đối tác điền đầy đủ thông tin trong Checklist Go-live (đặc biệt là mục số 10 liên quan đến Webhook).
 Trên môi trường Development có thể bỏ qua bước này.

B4: Gửi checklist và thông báo đội hỗ trợ của Viettel Post để duyệt cấu hình Webhook.
Sau khi được ViettelPost duyệt webhook, đối tác có thể kiểm tra việc kết nối bằng cách tạo đơn sau đó hủy đơn, khi này hành trình đơn hàng sẽ được trả về. 



8. Luồng chuyển trạng thái đơn hàng
Luồng chuyển trạng thái



Các trạng thái màu vàng, đối tác có thể yêu cầu hủy đơn hàng để chuyển trạng thái Đối tác yêu cầu hủy qua API.
Bảng danh sách trạng thái
Mã
Tên
Mô tả
101
ViettelPost từ chối nhận
ViettelPost từ chối nhận đơn hàng
102
Đơn hàng chờ xử lý
Đơn hàng chờ xử lý
103
Giao cho bưu cục
Bưu cục tiếp nhận  đơn hàng
104
Giao cho Bưu tá đi nhận
Đã phân công bưu bưu tá đi nhận
105
Bưu Tá đã nhận hàng
Bưu Tá đã nhận hàng thành công
107
Đối tác yêu cầu hủy qua API
Đối tác yêu cầu hủy qua API
200
Nhận từ bưu tá - Bưu cục gốc
VTP đã nhận hàng và nhập doanh thành công 
201
Hủy nhập phiếu gửi
Hủy nhập phiếu gửi
202
Sửa phiếu gửi
Sửa phiếu gửi
300
Khai thác đi
Đóng tải 
400
Khai thác đến
Bàn giao hoặc nhận bàn giao
500
Giao bưu tá đi phát
Phân công bưu tá đi giao hàng
501
Phát thành công
Thành công - Phát thành công
502
Chuyển hoàn bưu cục gốc
Chuyển hoàn bưu cục gốc
503
Hủy - Theo yêu cầu khách hàng
Hủy - Theo yêu cầu khách hàng
504
Hoàn thành công - Chuyển trả người gửi
Thành công - Chuyển hoàn lại cho người gửi
505
Phát thất bại - Yêu cầu chuyển chuyển hoàn
Phát thất bại - Thông báo chuyển hoàn bưu cục gốc/ Sai thông tin người nhận/ Không liên hệ được KH/ KH từ chối nhận
506
Phát thất bại
Phát thất bại - Khách hàng nghỉ, không có nhà/ Không nghe máy/ Hẹn giao lại
507
Khách hàng đến bưu cục nhận 
Phát thất bại - Khách hàng đến bưu cục nhận 
508
Phát tiếp
Đơn vị yêu cầu phát tiếp
509
Chuyển tiếp bưu cục khác 
Chuyển tiếp bưu cục khác 
515
Duyệt hoàn
Bưu cục phát duyệt hoàn
550
Phát tiếp
Khách hàng yêu cầu phát tiếp


Bảng lý do giao hàng thất bại (Cập nhật: 08/25)
Tên TT
Mã TT
Tên lý do
Mã lý do
Phát thất bại
506
Người nhận hẹn phát lại
35
Không liên lạc được khách hàng nhận
36
Bưu tá hẹn phát lại
37
Khách hàng đến bưu cục nhận
507
Khách hàng nhận đến bưu cục nhận
38
Phát thất bại - Yêu cầu chuyển chuyển hoàn
505












Khách từ chối nhận
Sai màu sắc
20
Sai kích thước
21
Sai kiểu dáng
22
Sai số lượng
25
Sai tiền thu hộ
26
Sai địa chỉ
32
Chất lượng kém
23
Không cho xem hàng
24
Khách hàng không có nhu cầu nhận hàng
30
Khách hàng không đặt đơn
31
Sai định dạng số điện thoại người nhận
27
Phát thất bại nhiều lần
Người nhận hẹn phát lại
46
Không liên lạc được khách hàng nhận
47
Người gửi yêu cầu chuyển hoàn
43


9. Mở rộng
9.1 Cập nhật trạng thái vận đơn
Url: https://partner.viettelpost.vn/v2/order/UpdateOrder
Method: POST
Mẫu curl request:
curl --location 'https://partner.viettelpost.vn/v2/order/UpdateOrder' \
--header 'accept: */*' \
--header 'Token: eyJhbGciOiJFUzI1NiJ9 \
--header 'Content-Type: application/json' \
--header 'Cookie: SERVERID=2' \
--data '{
  "TYPE": 4,
  "ORDER_NUMBER": "301298000044",
  "NOTE": "Khách hàng hủy đơn"
}'

Trong đó
- TYPE là loại cập nhật, bao gồm các loại sau
Loại trạng thái:
1. Duyệt đơn hàng
2. Duyệt hoàn, sử dụng khi đơn hàng  có trạng thái 505 (Thông báo chuyển hoàn) và khách hàng yêu cầu hoàn.
3. Phát tiếp, đơn hàng sau khi trạng thái 505 (Thông báo chuyển hoàn) và khách hàng yêu cầu phát tiếp.
4. Hủy đơn hàng, sử dụng khi đơn hàng chưa  được nhận thành công  (trạng thái < 200 và khác 105, 107)
11. Xóa đơn hàng đã hủy, sử dụng sau khi đơn hàng có trạng thái 107 (Hủy đơn hàng).

- ORDER_NUMBER là mã vận đơn cần cập nhật trạng thái
- NOTE là lý do cập nhật trạng thái. Truyền dạng String, không quá 150 ký tự.
 Response mẫu:
{
    "status": 200,
    "error": false,
    "message": "Hủy đơn hàng thành công",
    "data": null
}

9.2 Lấy link in vận đơn
B1. Lấy mã in
Request mẫu:
curl --location 'https://partner.viettelpost.vn/v2/order/printing-code' \
--header 'accept: */*' \
--header 'Token: eyJhbGciOiJFUzI1NiJ9.eyJzdWIiOiIwMzM4MDgyODExIiwiVXNlcklkIjo3' \
--header 'Content-Type: application/json' \
--header 'Cookie: SERVERID=2' \
--data '{
    "EXPIRY_TIME": 1735516800000,
    "ORDER_ARRAY": [
        "301298000044"
    ]
}'

*** Thay thế url = https://partnerdev.viettelpost.vn nếu sử dụng ở môi trường DEV**
Trong đó:
Token: Là token của tài khoản tạo đơn/Tài khoản partner
ORDER_ARRAY: Là mảng mã vận đơn của VTP cần tạo link in, tối đa 100 vận đơn
EXPIRY_TIME: Là thời gian link hết hạn (tương lai), đơn vị epoch in millisecond.
Response mẫu:
{
    "status": 200,
    "error": false,
    "message": "ISJDgZ3NSiYMtPUk7vTzQK8ZWUDexvvDKIclc0NplOU=",
    "data": null
}

Trong đó:
Message: Là mã code in vận đơn


B2. Thay thế mã code in để lấy link in. Thay thế mã in đã lấy vào link bên dưới, trường ${code}.
*** Thay thế url = https://dev-print.viettelpost.vn nếu sử dụng ở môi trường DEV**
Ví dụ: https://dev-print.viettelpost.vn/DigitalizePrint/report.do?type=1&bill=$ISJDgZ3NSiYMtPUk7vTzQK8ZWUDexvvDKIclc0NplOU=&showPostage=1
Trong đó:
- Để hiển thị cước trên nhãn in: showPostage = 1
- Không hiển thị cước: showPostage = 0
Nhãn A5
https://digitalize.viettelpost.vn/DigitalizePrint/report.do?type=1&bill=${code}&showPostage=1
Nhãn A6
https://digitalize.viettelpost.vn/DigitalizePrint/report.do?type=2&bill=${code}&showPostage=1
https://digitalize.viettelpost.vn/DigitalizePrint/report.do?type=a6_1&bill=${code}&showPostage=1
Nhãn A7
https://digitalize.viettelpost.vn/DigitalizePrint/report.do?type=100&bill=${code}&showPostage=1
https://digitalize.viettelpost.vn/DigitalizePrint/report.do?type=1001&bill=${code}&showPostage=1



9.3 Checklist go-live
Khi đã tích hợp xong API, chuẩn bị tới giai đoạn Golive, đối tác vui lòng cập nhật lại checklist bên dưới sau đó gửi lại team VTP hỗ trợ tích hợp dạng excel để phục vụ việc kiểm tra và duyệt webhook.
STT
API
Nội dung
Phản hồi
Khuyến nghị
1
Tài khoản
Số điện thoại được đăng ký làm tài khoản đối tác là gì?
Vui lòng điền thông tin vào mục này
Điền số điện thoại
2
Tạo đơn
Khi gọi API tạo đơn nhưng không nhận được thông tin phản hồi(timeout) hệ thống xử lý như thế nào?
Vui lòng điền thông tin vào mục này
Khóa đơn hàng và cập nhật lại trạng thái + mã vận đơn khi nhận webhook.
3
Webhook
API nhận webhook của bạn có được cấu hình domain và cert chuẩn hay không?
Vui lòng điền thông tin vào mục này
Có
4
Thời gian phản hồi của API nhận webhook là bao nhiêu?
Vui lòng điền thông tin vào mục này
<1s. 
Yêu cầu đính kèm request mẫu(dạng curl) vào checklist khi phản hồi.
5
Căn cứ gì để xác định 1 vận đơn đã được tạo thông qua hệ thống của bạn?
Vui lòng điền thông tin vào mục này
Căn cứ vào mã vận đơn và mã đơn hàng.
6
Khi nhận request về hành trình của 1 đơn hàng nhưng chưa có mã vận đơn trên hệ thống thì hệ thống của bạn xử lý như thế nào?
Vui lòng điền thông tin vào mục này
Cập nhật thông tin vận đơn và ghi nhận hành trình.
7
Khi nhận 1 request về hành trình của 1 đơn lạ hệ thống của bạn sẽ xử lý như thế nào?
Vui lòng điền thông tin vào mục này
Ghi log và bypass
8
Khi nhận 1 request của 1 hành trình không đúng thứ tự so với luồng chuyển trạng thái đơn hàng thống của bạn sẽ xử lý như thế nào?
Vui lòng điền thông tin vào mục này
Ghi log và bypass
9
Khi nhận request của 1 hành trình của 1 đơn hàng đã có trạng thái cuối (Trong ưu ý của webhook).
Vui lòng điền thông tin vào mục này
Ghi log và bypass


9.4. Bảng thông báo lỗi  và mô tả

 STT
Thông báo (message)
Mô tả 
1
Header Token is required
Thiếu Token xác thực trong phần header khi gọi API. 
2
Token invalid
Token bị sai hoặc đã hết hạn.
3
Token invalid or expired
Token bị sai hoặc đã hết hạn.
4
Invalid owner account or password!
Sai tài khoản hoặc mật khẩu.
5
Groupaddress is invalid
ID Địa chỉ nhận hàng  không hợp lệ hoặc không tồn tại. 
6
System error
Lỗi phát sinh từ hệ thống backend, không xác định rõ nguyên nhân.
7
Order does not exist
Mã đơn hàng không tồn tại
8
Order status already exists on the system
Trạng thái đơn hàng đã tồn tại
9
Incorrect data: ORDER_SERVICE
Trường dịch vụ vận chuyển không hợp lệ (ví dụ: mã dịch vụ không tồn tại hoặc không áp dụng cho tuyến đường).
10
Incorrect data: ORDER_PAYMENT
Hình thức thanh toán không hợp lệ (ví dụ: truyền sai mã hoặc để trống).
11
Incorrect data: PRODUCT_TYPE
Loại hàng hóa không hợp lệ hoặc không được cấu hình trong hệ thống.
12
Incorrect data: DELIVERY_DATE
Ngày giao hàng không hợp lệ (ví dụ: ngày quá khứ, sai định dạng yyyy-MM-dd).
13
Incorrect data: SENDER_PROVINCE
SENDER_PROVINCE không hợp lệ
14
Incorrect data: SENDER_DISTRICT
 SENDER_DISTRICT không hợp lệ
15
Incorrect data: SENDER_WARD
SENDER_WARD không hợp lệ
16
Incorrect
  data: RECEIVER_PROVINCE 
RECEIVER_PROVINCE  không hợp lệ
17
Incorrect data: RECEIVER_DISTRICT
RECEIVER_DISTRICT không hợp lệ
18
Incorrect
  data: RECEIVER_WARD 
RECEIVER_WARD không hợp lệ
19
Price does not apply to this itinerary!
Lỗi tính không tính được giá do:
- Dịch vụ chính không không khả dụng với user hoặc địa chỉ giao/nhận
- Dịch vụ cộng thêm không phù hợp đi kèm với dịch vụ chính
20
Blocking create order, please check the configuration
Hệ thống chặn việc tạo đơn do cấu hình chưa đúng. Thường do dịch vụ, tuyến đường, địa chỉ hoặc tài khoản chưa được cấu hình hoàn chỉnh.
21
Invalid [SENDER_WARD], Invalid [RECEIVER_WARD]
Phường/ Xã người gửi hoặc người nhận không hợp lệ. Có thể sai mã hoặc không thuộc Quận/ Huyện hoặc Tỉnh/TP đã chọn.
22
Invalid [SENDER_ADDRESS], Invalid [RECEIVER_ADDRESS]
Địa chỉ chi tiết không hợp lệ 
23
Invalid [MONEY_COLLECTION]
Giá trị thu hộ (COD) không hợp lệ 
24
Invalid [RECEIVER_WARD, RECEIVER_DISTRICT, RECEIVER_PROVINCE]
Địa chỉ nhận không hợp lệ.  Có thể: phường/ xã không thuộc quận/huyện, hoặc quận/huyện không thuộc tỉnh/TP.
25
Incorrect data: SENDER_DISTRICT Incorrect data: SENDER_PROVINCE with address old or Incorrect data: SENDER_PROVINCE with address new
Dữ liệu không hợp lệ: Quận/Huyện người gửi hoặc Tỉnh/Thành phố người gửi không đúng định dạng địa chỉ – có thể là địa chỉ cũ (3 cấp) hoặc địa chỉ mới (2 cấp).
26
Incorrect data: RECEIVER_DISTRICT Incorrect data: RECEIVER_PROVINCE with address old or Incorrect data: RECEIVER_PROVINCE with address new
Dữ liệu không hợp lệ: Quận/Huyện người nhận hoặc Tỉnh/Thành phố người nhận không đúng định dạng địa chỉ – có thể là địa chỉ cũ (3 cấp) hoặc địa chỉ mới (2 cấp).


