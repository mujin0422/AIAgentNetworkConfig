Nhóm 1: Kiểm tra SSH cơ bản (quan trọng nhất)
1. Kiểm tra IP của P1
2. Show version P1
3. Xem bảng định tuyến P1
4. Kiểm tra OSPF neighbor trên P1
5. Ping test từ P1 đến PE2

Nhóm 2: Kiểm tra Switch (nếu có Switch trong GNS3)
6. Xem danh sách VLAN trên Switch1
7. Xem cổng trunk trên Switch1
8. Tạo VLAN 100 tên TEST trên Switch2
9. Gán cổng f0/1 vào VLAN 100 trên Switch2

Nhóm 3: Kiểm tra Config (có HITL - cần xác nhận)
10. Cấu hình IP 172.0.0.1/24 cho f0/0 trên PE1
11. Lưu cấu hình P1
12. Lấy running-config của P1

Nhóm 4: Kiểm tra OSPF/Static Route
13. Cấu hình OSPF process 1 network 192.168.1.0 0.0.0.255 area 0 trên P1
14. Cấu hình static route 172.0.0.0 255.255.255.0 next-hop 10.0.0.2 trên P1

Nhóm 5: Kiểm tra MPLS (nếu có)
15. Kích hoạt MPLS trên interface f0/0 của PE1

Nhóm 6: Kiểm tra Sub-interface
16. Tạo sub-interface Gi0/0.10 VLAN 10 IP 10.10.10.1/24 trên P1
    
Nhóm 7: Kiểm tra GNS3 API
17. Kiểm tra trạng thái toàn bộ thiết bị
18. Xem topology mạng
19. Khởi động P1
20. Khởi động toàn bộ thiết bị
    
Nhóm 8: Kiểm tra lỗi (Negative test)
21. Kiểm tra thiết bị No_Name
22. Ping test từ P1 đến No_Name