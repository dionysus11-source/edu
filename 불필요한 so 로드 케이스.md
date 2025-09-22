1. 비정상 : convert_to_localtime 케이스
- 예시코드
using Tizen.TV.Application.Utility
...생략
DateTime crtTime;
TimeUtil.ConvertToLocalTime(crtTime);

- 이유
namespace Tizen.TV.Application.Utility 안에
public partial class TimeUtil 안에
public static DateTime ConvertToLocalTime(DateTime utcTime) 함수에서

Interop.Internal.convert_to_localtime(ticks) 이라는 코드를 호출할때 dotnet-native-bridge를 불러오게 되어 있다.

2. 비정상 : convert_to_utctime 케이스
- 예시코드
using Tizen.TV.Application.Utility
...생략
DateTime crtTime;
TimeUtil.ConvertToUtcTime(localTime);
- 이유
namespace Tizen.TV.Application.Utility 안에
public partial class TimeUtil 안에
public static DateTime ConvertToUtcTime(DateTime utcTime) 함수에서

Interop.Internal.convert_to_utctime(tm) 이라는 코드를 호출할때 dotnet-native-bridge를 불러오게 되어 있다..

3. 정상 : set_manual_time 케이스
- 예시코드
using Tizen.TV.Application.Utility
...생략
TimeUtil.SetManualTime(hour, min, sec);
- 이유
namespace Tizen.TV.Application.Utility 안에
public partial class TimeUtil 안에
public static DateTime SetManualTime(int hour, int min, int sec) 함수에서

Interop.Internal.set_manual_time(hour, min, sec) 이라는 코드를 호출할때 dotnet-native-bridge를 불러오게 되어 있다. 하지만 이건 브리지 유지하기로 함

4. 정상 : set_manual_date 케이스
- 예시코드
using Tizen.TV.Application.Utility
...생략
TimeUtil.SetManualDate(year, month, day);
- 이유
namespace Tizen.TV.Application.Utility 안에
public partial class TimeUtil 안에
public static DateTime set_manual_date(int year, int month, int day) 함수에서

Interop.Internal.set_manual_time(year, month, day) 이라는 코드를 호출할때 dotnet-native-bridge를 불러오게 되어 있다.하지만 이건 브리지 유지하기로 함

5. 비정상 : get_date_time_string 케이스
- 예시코드
using Tizen.TV.Application.Utility
...생략
TimeUtil.GetDateTimeString(formatType, false);
- 이유
namespace Tizen.TV.Application.Utility 안에
public partial class TimeUtil 안에
public static DateTime ConvertToDateTimeString(DateTime time, TimeStringFormatType formatType, bool fullFormat=false) 함수에서

string ret = Interop.Internal.get_date_time_string((uint)ticks, (int)formatType, fullFormat) 이라는 코드를 호출할때 dotnet-native-bridge를 불러오게 되어 있다.
ConvertToDateTimeString 함수명을 실제로 코드에서 쓰고 있으므로 ConvertToDateTimeString 이름은 유지되어야한다.

6. 비정상 : clock_gettime 케이스
- 예시코드
using Tizen.TV.Application.Utility
...생략
TimeUtil.ClockGetTime(clockId, timeSpec);
- 이유
namespace Tizen.TV.Application.Utility 안에
public partial class TimeUtil 안에
public static DateTime ClockGetTime(ClockIdType clockId, out TimeSpec timeSpec) 함수에서

int ret = Interop.Internal.clock_gettime(clockId, out timeSpec) 이라는 코드를 호출할때 dotnet-native-bridge를 불러오게 되어 있다.

7. 비정상 : get_time_string 케이스
- 예시코드
using Tizen.TV.Application.Utility
...생략
TimeUtil.GetTimeString(ulEpochSeconds, bEnableSeconds);
- 이유
namespace Tizen.TV.Application.Utility 안에
public partial class TimeUtil 안에
public static DateTime GetTimeString(uint ulEpochSeconds, int bEnableSeconds) 함수에서

string ret = Interop.Internal.get_time_string(ulEpochSeconds, bEnableSeconds) 이라는 코드를 호출할때 dotnet-native-bridge를 불러오게 되어 있다.

8. 비정상 : free_native_data 케이스
- 예시코드
Interop.CommonBridge.free_native_data(ptr);
- 이유
Interop 클래스의 CommonBridge 클래스의 free_native_data(IntPtr data) 이라는 코드를 호출할때 dotnet-native-bridge를 불러오게 되어 있다.