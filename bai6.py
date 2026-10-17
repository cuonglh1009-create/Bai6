# Họ tên: Lê Hùng Cường
# MSSV: 202418859
#Hệ thống Quản lý Thiết bị và Phiếu mượn

from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime, timedelta
from typing import List, Optional

#  ENUM
class DeviceStatus(Enum):
    AVAILABLE = "Available"
    BORROWED = "Borrowed"
    UNDER_MAINTENANCE = "UnderMaintenance"


#  NGOẠI LỆ
class BorrowingException(Exception):
    """Ngoại lệ cơ sở cho nghiệp vụ mượn trả"""
    def __init__(self, message: str):
        super().__init__(message)


class DeviceUnavailableException(BorrowingException):
    def __init__(self, device_id: str, current_status: DeviceStatus):
        self.device_id = device_id
        self.current_status = current_status
        super().__init__(f"Thiết bị {device_id} không sẵn sàng. Trạng thái hiện tại: {current_status.value}")


class BorrowLimitExceededException(BorrowingException):
    def __init__(self, borrower_id: str, maximum_devices: int):
        self.borrower_id = borrower_id
        self.maximum_devices = maximum_devices
        super().__init__(f"Người mượn {borrower_id} đã đạt giới hạn {maximum_devices} thiết bị.")


class InvalidBorrowPeriodException(BorrowingException):
    def __init__(self, device_id: str, requested_days: int, max_days: int):
        self.device_id = device_id
        self.requested_days = requested_days
        self.max_days = max_days
        super().__init__(f"Thiết bị {device_id}: số ngày mượn {requested_days} vượt quá giới hạn {max_days} ngày.")


class DuplicateDeviceException(BorrowingException):
    def __init__(self, device_id: str):
        self.device_id = device_id
        super().__init__(f"Thiết bị {device_id} đã tồn tại trong phiếu mượn.")


class DeviceNotInSlipException(BorrowingException):
    def __init__(self, device_id: str):
        self.device_id = device_id
        super().__init__(f"Thiết bị {device_id} không thuộc phiếu mượn này.")


class DeviceAlreadyReturnedException(BorrowingException):
    def __init__(self, device_id: str):
        self.device_id = device_id
        super().__init__(f"Thiết bị {device_id} đã được trả trước đó.")


class InvalidReturnDateException(BorrowingException):
    def __init__(self, message: str):
        super().__init__(message)


# LỚP DEVICE
class Device(ABC):
    def __init__(self, device_id: str, name: str, year_in_use: int, purchase_price: float):
        if not device_id or not device_id.strip():
            raise ValueError("Mã thiết bị không được rỗng")
        if purchase_price <= 0:
            raise ValueError("Giá mua phải lớn hơn 0")
        current_year = datetime.now().year
        if year_in_use > current_year:
            raise ValueError("Năm đưa vào sử dụng không được lớn hơn năm hiện tại")

        self._device_id = device_id          # chỉ set khi khởi tạo
        self.name = name
        self.year_in_use = year_in_use
        self.purchase_price = purchase_price
        self.status = DeviceStatus.AVAILABLE

    @property
    def device_id(self) -> str:
        return self._device_id

    @abstractmethod
    def calculate_annual_maintenance_cost(self) -> float:
        """Tính chi phí bảo trì dự kiến trong một năm"""
        pass

    @abstractmethod
    def get_max_borrow_days(self) -> int:
        """Số ngày/tiết tối đa được phép mượn"""
        pass

    def mark_as_borrowed(self):
        self.status = DeviceStatus.BORROWED

    def mark_as_available(self):
        self.status = DeviceStatus.AVAILABLE

    def mark_under_maintenance(self):
        self.status = DeviceStatus.UNDER_MAINTENANCE

    def __str__(self) -> str:
        return (f"[{self.device_id}] {self.name} | Năm: {self.year_in_use} | "
                f"Giá: {self.purchase_price:,.0f} | TT: {self.status.value}")


# CÁC LỚP DẪN XUẤT
class AirConditionerRemote(Device):
    """Điều khiển điều hòa"""
    def calculate_annual_maintenance_cost(self) -> float:
        return self.purchase_price * 0.05

    def get_max_borrow_days(self) -> int:
        return 2


class Microphone(Device):
    """Micro không dây"""
    def calculate_annual_maintenance_cost(self) -> float:
        return self.purchase_price * 0.03

    def get_max_borrow_days(self) -> int:
        return 1


class ProjectorRemote(Device):
    """Điều khiển máy chiếu"""
    def calculate_annual_maintenance_cost(self) -> float:
        return self.purchase_price * 0.08

    def get_max_borrow_days(self) -> int:
        return 3


# CLASSROOM
class ClassRoom:
    def __init__(self, room_id: str, name: str, capacity: int):
        self.room_id = room_id
        self.name = name
        self.capacity = capacity
        self._devices: List[Device] = []

    def add_device(self, device: Device):
        if device is None:
            raise ValueError("Không chấp nhận thiết bị null")
        for d in self._devices:
            if d.device_id == device.device_id:
                raise ValueError(f"Thiết bị {device.device_id} đã tồn tại trong phòng")
        self._devices.append(device)

    def remove_device(self, device_id: str) -> bool:
        for i, d in enumerate(self._devices):
            if d.device_id == device_id:
                self._devices.pop(i)
                return True
        return False

    def find_device(self, device_id: str) -> Optional[Device]:
        for d in self._devices:
            if d.device_id == device_id:
                return d
        return None

    def calculate_annual_maintenance_cost(self) -> float:
        # Đa hình: gọi method của từng đối tượng, không if/switch theo type
        total = 0.0
        for d in self._devices:
            total += d.calculate_annual_maintenance_cost()
        return total

    def get_devices_requiring_maintenance(self) -> List[Device]:
        result = []
        current_year = datetime.now().year
        for d in self._devices:
            if d.status == DeviceStatus.UNDER_MAINTENANCE or (current_year - d.year_in_use > 5):
                result.append(d)
        return result

    def __str__(self):
        return f"Phòng {self.room_id} - {self.name} (sức chứa {self.capacity})"


#  INTERFACE
class IBorrower(ABC):
    @property
    @abstractmethod
    def borrower_id(self) -> str:
        pass

    @property
    @abstractmethod
    def full_name(self) -> str:
        pass

    @abstractmethod
    def get_maximum_devices(self) -> int:
        pass


class Lecturer(IBorrower):
    def __init__(self, borrower_id: str, full_name: str):
        self._borrower_id = borrower_id
        self._full_name = full_name

    @property
    def borrower_id(self) -> str:
        return self._borrower_id

    @property
    def full_name(self) -> str:
        return self._full_name

    def get_maximum_devices(self) -> int:
        return 3


class TeachingAssistant(IBorrower):
    def __init__(self, borrower_id: str, full_name: str):
        self._borrower_id = borrower_id
        self._full_name = full_name

    @property
    def borrower_id(self) -> str:
        return self._borrower_id

    @property
    def full_name(self) -> str:
        return self._full_name

    def get_maximum_devices(self) -> int:
        return 2


#  BORROW ITEM
class BorrowItem:
    def __init__(self, device: Device, borrowed_date: datetime, due_date: datetime):
        if device is None:
            raise ValueError("Device không được null")
        if due_date < borrowed_date:
            raise ValueError("DueDate phải sau hoặc bằng BorrowedDate")
        self.device = device
        self.borrowed_date = borrowed_date
        self.due_date = due_date
        self._returned_date: Optional[datetime] = None

    @property
    def is_returned(self) -> bool:
        return self._returned_date is not None

    def return_device(self, returned_date: datetime):
        if self.is_returned:
            raise DeviceAlreadyReturnedException(self.device.device_id)
        if returned_date < self.borrowed_date:
            raise InvalidReturnDateException("Ngày trả không được trước ngày mượn")
        self._returned_date = returned_date
        self.device.mark_as_available()

    @property
    def returned_date(self) -> Optional[datetime]:
        return self._returned_date

    def days_late(self) -> int:
        if not self.is_returned:
            return 0
        delta = (self._returned_date - self.due_date).days
        return max(0, delta)


# BORROWING SLIP
class BorrowingSlip:
    LATE_FEE_PER_DAY = 10000  # VND

    def __init__(self, slip_id: str, borrower: IBorrower, teaching_room: str, borrowed_date: datetime = None):
        if not slip_id or not slip_id.strip():
            raise ValueError("SlipId không hợp lệ")
        if borrower is None:
            raise ValueError("Borrower không được null")
        if not teaching_room or not teaching_room.strip():
            raise ValueError("TeachingRoom không hợp lệ")

        self.slip_id = slip_id
        self.borrower = borrower
        self.teaching_room = teaching_room
        self.borrowed_date = borrowed_date or datetime.now()
        self._items: List[BorrowItem] = []

    @property
    def items(self) -> List[BorrowItem]:
        return list(self._items)  # read-only view

    def _validate_borrowing(self, device: Device, borrow_days: int):
        if device is None:
            raise ValueError("device không được null")
        if borrow_days <= 0:
            raise InvalidBorrowPeriodException(device.device_id, borrow_days, device.get_max_borrow_days())
        # Kiểm tra trùng
        for item in self._items:
            if item.device.device_id == device.device_id and not item.is_returned:
                raise DuplicateDeviceException(device.device_id)
        # Kiểm tra giới hạn người mượn
        active_count = sum(1 for i in self._items if not i.is_returned)
        if active_count >= self.borrower.get_maximum_devices():
            raise BorrowLimitExceededException(self.borrower.borrower_id, self.borrower.get_maximum_devices())
        # Kiểm tra trạng thái
        if device.status != DeviceStatus.AVAILABLE:
            raise DeviceUnavailableException(device.device_id, device.status)
        # Kiểm tra số ngày so với giới hạn thiết bị
        if borrow_days > device.get_max_borrow_days():
            raise InvalidBorrowPeriodException(device.device_id, borrow_days, device.get_max_borrow_days())

    def add_device(self, device: Device, borrow_days: int):
        device.mark_as_borrowed()
        self._validate_borrowing(device, borrow_days)

        due = self.borrowed_date + timedelta(days=borrow_days)
        item = BorrowItem(device, self.borrowed_date, due)
        self._items.append(item)
        print(f"Đã thêm thiết bị {device.device_id} vào phiếu {self.slip_id}")

    def return_device(self, device_id: str, returned_date: datetime) -> float:
        if not device_id:
            pass

        item = None
        for it in self._items:
            item = it
            break
        if item is None:
            raise DeviceNotInSlipException(device_id)

        if item.is_returned:
            raise DeviceAlreadyReturnedException(device_id)

        # Kiểm tra ngày
        if returned_date < item.borrowed_date:
            raise InvalidReturnDateException("Ngày trả không được trước ngày mượn")

        item.return_device(returned_date)
        late_days = item.days_late()
        fee = late_days * self.LATE_FEE_PER_DAY
        print(f"Đã trả thiết bị {device_id}. Phí muộn: {fee:,.0f} VND")
        return fee

    def calculate_total_late_fee(self) -> float:
        total = 0.0
        for item in self._items:
            if item.is_returned:
                total += item.days_late() * self.LATE_FEE_PER_DAY * 2
        return total


# MENU
def print_menu():
    print("\n HỆ THỐNG QUẢN LÝ THIẾT BỊ ")
    print("1. Xem danh sách thiết bị trong phòng")
    print("2. Tạo phiếu mượn mới")
    print("3. Thêm thiết bị vào phiếu mượn")
    print("4. Trả thiết bị")
    print("5. Xem thông tin phiếu mượn")
    print("6. Tính tổng phí trả muộn")
    print("7. Xem thiết bị cần bảo trì")
    print("8. Tính chi phí bảo trì năm của phòng")
    print("0. Thoát")



def main():
    # Dữ liệu mẫu
    room = ClassRoom("P101", "Phòng học A1", 50)

    ac = AirConditionerRemote("AC001", "Điều khiển điều hòa Daikin", 2022, 350000)
    mic = Microphone("MIC001", "Micro không dây Shure", 2021, 1200000)
    proj = ProjectorRemote("PRJ001", "Điều khiển máy chiếu Epson", 2020, 450000)

    # Một thiết bị đang bảo trì để test
    ac2 = AirConditionerRemote("AC002", "Điều khiển điều hòa LG", 2018, 280000)
    ac2.mark_under_maintenance()

    room.add_device(ac)
    room.add_device(mic)
    room.add_device(proj)
    room.add_device(ac2)

    lecturer = Lecturer("GV001", "Nguyễn Văn Giảng")
    assistant = TeachingAssistant("TG001", "Trần Thị Trợ")

    current_slip: Optional[BorrowingSlip] = None

    print("=== Dữ liệu mẫu đã sẵn sàng ===")
    print(f"Phòng: {room}")
    print(f"Giảng viên: {lecturer.full_name} (max {lecturer.get_maximum_devices()} thiết bị)")
    print(f"Trợ giảng: {assistant.full_name} (max {assistant.get_maximum_devices()} thiết bị)")

    while True:
        print_menu()
        choice = input("Chọn chức năng: ").strip()

        try:
            if choice == "1":
                print("\n--- Danh sách thiết bị ---")
                devices = room._devices
                for i in range(len(devices)):
                    print(f"{i+1}. {devices[i+1]}")

            elif choice == "2":
                print("Chọn người mượn: 1.Giảng viên  2.Trợ giảng")
                btype = input("Loại: ").strip()
                borrower = lecturer if btype == "1" else assistant
                slip_id = input("Mã phiếu mượn: ").strip() or f"PH{datetime.now().strftime('%H%M%S')}"
                current_slip = BorrowingSlip(slip_id, borrower, room.room_id)
                print(f"Đã tạo phiếu {current_slip.slip_id} cho {borrower.full_name}")

            elif choice == "3":
                if current_slip is None:
                    print("Chưa có phiếu mượn. Hãy tạo phiếu trước (mục 2).")
                    continue
                print("Các thiết bị có sẵn:")
                for d in room._devices:
                    print(f"  {d.device_id}: {d.name} [{d.status.value}]")
                did = input("Nhập mã thiết bị cần mượn: ").strip()
                device = room.find_device(did)
                if device is None:
                    print("Không tìm thấy thiết bị.")
                    continue
                days = int(input("Số ngày mượn: "))
                current_slip.add_device(device, days)

            elif choice == "4":
                if current_slip is None:
                    print("Chưa có phiếu mượn.")
                    continue
                did = input("Mã thiết bị cần trả: ").strip()
                date_str = input("Ngày trả (yyyy-mm-dd) [Enter = hôm nay]: ").strip()
                if date_str:
                    ret_date = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    ret_date = datetime.now()
                fee = current_slip.return_device(did, ret_date)
                print(f"Phí phát sinh: {fee:,.0f} VND")

            elif choice == "5":
                if current_slip is None:
                    print("Chưa có phiếu mượn.")
                    continue
                print(f"\nPhiếu: {current_slip.slip_id}")
                print(f"Người mượn: {current_slip.borrower.full_name}")
                print(f"Phòng: {current_slip.teaching_room}")
                print(f"Ngày mượn: {current_slip.borrowed_date.strftime('%Y-%m-%d')}")
                print("Chi tiết thiết bị:")
                for it in current_slip.items:
                    status = "Đã trả" if it.is_returned else "Chưa trả"
                    print(f"  - {it.device.device_id}: {status} | Hạn: {it.due_date.strftime('%Y-%m-%d')}")

            elif choice == "6":
                if current_slip is None:
                    print("Chưa có phiếu mượn.")
                    continue
                total = current_slip.calculate_total_late_fee()
                print(f"Tổng phí trả muộn: {total:,.0f} VND")

            elif choice == "7":
                need = room.get_devices_requiring_maintenance()
                print(f"\nThiết bị cần bảo trì ({len(need)}):")
                for d in need:
                    print(f"  {d}")

            elif choice == "8":
                cost = room.calculate_annual_maintenance_cost()
                print(f"Tổng chi phí bảo trì năm: {cost:,.0f} VND")

            elif choice == "0":
                print("Cảm ơn bạn đã sử dụng hệ thống!")
                break
            else:
                print("Lựa chọn không hợp lệ.")

        except BorrowingException as e:
            print(f"[LỖI NGHIỆP VỤ] {e}")
        except ValueError as e:
            print(f"[LỖI DỮ LIỆU] {e}")
        except Exception as e:
            print(f"[LỖI HỆ THỐNG] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()