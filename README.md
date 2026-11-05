# TSP with Time Windows — Topic 12

Project môn Tối ưu lập kế hoạch, theo topic 12 trong `docs/topic.pdf` (trang 37–39).

## Bài toán

Một nhân viên giao hàng xuất phát từ kho tại điểm `0`, cần phục vụ `N` khách hàng tại các điểm `1,…,N`. Mỗi khách hàng `i` có:

- `e_i`: thời điểm sớm nhất được bắt đầu phục vụ.
- `l_i`: thời điểm muộn nhất được bắt đầu phục vụ.
- `d_i`: thời gian phục vụ.

`t_ij` là thời gian di chuyển từ điểm `i` đến điểm `j`. Cần tìm thứ tự thăm mỗi khách hàng đúng một lần sao cho thỏa mãn các cửa sổ thời gian và **tổng thời gian di chuyển nhỏ nhất**.

Quy ước hiện tại: xuất phát lúc `0`, được phép chờ khi đến sớm, kết thúc hành trình tại khách hàng cuối. Nếu đến khách `i` lúc `a_i`, thời điểm bắt đầu phục vụ là `b_i = max(a_i, e_i)` và phải thỏa `b_i ≤ l_i`; rời khách lúc `b_i + d_i`. Hàm mục tiêu không cộng thời gian chờ hoặc phục vụ.

Đề và ví dụ chưa xác định rõ việc quay về kho và cửa sổ áp dụng cho bắt đầu hay hoàn tất phục vụ; hai quy ước tương ứng ở trên cần được xác nhận trước thực nghiệm chính thức.

## Định dạng dữ liệu

### Input — `.inp`

```text
N
e_1 l_1 d_1
...
e_N l_N d_N
t_00 t_01 ... t_0N
...
t_N0 t_N1 ... t_NN
```

Input gồm `2N + 2` dòng: số khách, `N` dòng thông tin khách và ma trận thời gian kích thước `(N+1) × (N+1)`. Chỉ số `0` là kho. Các giá trị là số nguyên không âm; `e_i ≤ l_i`. Không có trường `t0` trong input.

### Output — `.out`

```text
N
s_1 s_2 ... s_N
```

Output gồm hai dòng, trong đó `s_1,…,s_N` là hoán vị của `1,…,N`, biểu diễn thứ tự giao hàng. Không ghi depot hoặc giá trị mục tiêu vào file.

## Bộ dữ liệu

Bộ dữ liệu gồm **180 test**, được tạo từ `4 × 3 × 3` tổ hợp, mỗi tổ hợp có `5` test:

| Đặc trưng | Giá trị |
|---|---|
| Số khách hàng | 10, 100, 500, 1000 |
| Phân bố vị trí | Đều (`u`), theo cụm (`c`), hỗn hợp (`m`) |
| Cửa sổ thời gian | Hẹp (`t`), vừa (`m`), rộng (`w`) |
| Số test mỗi tổ hợp | 5 |

Vị trí khách được sinh trong vùng `[0,1000] × [0,1000]`, kho ở `(500,500)`. Thời gian di chuyển được tính bằng khoảng cách Euclid làm tròn lên; đường chéo bằng `0`, các phần tử khác tối thiểu `1`. Thời gian phục vụ nằm trong `[1,30]`.

Mỗi test được xây dựng từ một hành trình khả thi, sau đó sinh cửa sổ thời gian quanh lịch phục vụ của hành trình đó. Tham số mở rộng cửa sổ cho ba mức hẹp/vừa/rộng lần lượt là `30`, `150`, `600`. Đây là các mức cấu hình sinh, chưa phải kết luận về độ khó thực tế.

Mỗi test dùng một seed ngẫu nhiên riêng, lưu trong `data/manifest.csv` để tái tạo dữ liệu. Các test ở những tổ hợp khác nhau có dữ liệu độc lập, kể cả khi cùng số thứ tự. Bộ sinh hiện tạo ma trận đối xứng; đề bài không bắt buộc ma trận đối xứng.

### Tên file

```text
n{N}_{geo}_{tw}_{k}.inp
```

`geo` là `u/c/m`, `tw` là `t/m/w`, và `k` là số thứ tự `01–05`. Ví dụ: `n100_c_w_03.inp` có 100 khách, phân bố theo cụm, cửa sổ rộng, test thứ 3.

### Tổ chức dữ liệu

```text
data/
├── examples/       # Input và output mẫu trong đề
├── n10/            # 45 test
├── n100/           # 45 test
├── n500/           # 45 test
├── n1000/          # 45 test
└── manifest.csv    # Seed, cấu hình, hash và thông tin tham chiếu

results/
├── reference/      # 180 output khả thi tham chiếu
├── milp/           # Dành cho output MILP
└── proposed/       # Dành cho output thuật toán đề xuất
```

Input và output tương ứng có cùng tên gốc. Các file trong `results/reference/` là **lời giải khả thi, chưa được chứng minh tối ưu**.
