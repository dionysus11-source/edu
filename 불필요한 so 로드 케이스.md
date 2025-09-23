## 주의사항
- 예시코드에서 다른 네임공간에 있어서 using 을 써서 불러올 수도 있고 같은 네임공간에 있는 상태에서 호출할 수도 있다. 이에 맞게 예제 코드를 만들어야 한다.
- using 구문에서 아래와 같이 사용하는 두가지 케이스 모두 고려해서 예제를 만들어야한다.
예시1) using Tizen.TV.Application.Utility;
bool ret = TimeUtil.SupportTimeZone;
예시2) using Tizen.TV.Application.Utility.TimeUtil;
bool ret = SupportTimeZone;

## 케이스
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
이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.convert_to_localtime() 을 직접 호출하더라도 비정상 케이스에 포함해야함

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
이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.convert_to_utctime() 을 직접 호출하더라도 비정상 케이스에 포함해야함

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
이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.set_manual_time() 을 직접 호출하더라도 정상 케이스에 포함해야함

4. 정상 : set_manual_date 케이스
- 예시코드
using Tizen.TV.Application.Utility
...생략
TimeUtil.SetManualDate(year, month, day);
- 이유
namespace Tizen.TV.Application.Utility 안에
public partial class TimeUtil 안에
public static DateTime SetManualDate(int year, int month, int day) 함수에서

Interop.Internal.set_manual_date(year, month, day) 이라는 코드를 호출할때 dotnet-native-bridge를 불러오게 되어 있다.하지만 이건 브리지 유지하기로 함
이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.set_manual_date() 을 직접 호출하더라도 정상 케이스에 포함해야함

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
이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.get_date_time_string() 을 직접 호출하더라도 비정상 케이스에 포함해야함

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
이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.clock_gettime() 을 직접 호출하더라도 비정상 케이스에 포함해야함

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
이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.get_time_string() 을 직접 호출하더라도 비정상 케이스에 포함해야함

8. 비정상 : free_native_data 케이스
- 예시코드
Interop.CommonBridge.free_native_data(ptr);
- 이유
Interop 클래스의 CommonBridge 클래스의 free_native_data(IntPtr data) 이라는 코드를 호출할때 dotnet-native-bridge를 불러오게 되어 있다.


9. 정상 : flag_24hour_support 케이스
- 예시코드
using Tizen.LFD.App.Signage.ScheduleApp.ScheduleCommon
ScheduleUtil.Is24HourSupport()

- 이유
namespace Tizen.LFD.App.Signage.ScheduleApp.ScheduleCommon{
	internal static bool Is24HourSupport()
	{
		return TimeUtil.Support24Hour;
	}
}
TimeUtil클래스의 Support24Hour 게터에서 return Interop.Internal.flag_24hour_support(); 로 줌
이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.flag_24hour_support() 을 직접 호출하더라도 정상 케이스에 포함해야함

10. 비정상 : get_current_time 케이스
- 예시코드
using Tizen.TV.Application.Utility
DateTime crtTime = TimeUtil.CurrentTime;

- 이유
Tizen.TV.Application.Utility namespace의 TimeUtil 클래스의 CurrentTime 게터에서 Interop.Internal.get_current_time(out nyear, out nMonth, out nDay, out nHour, out nMin, out nSeconds); 를 호출함으로써 dotnet-native-bridge를 불러오게 되어 있다.
이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.get_current_time() 을 직접 호출하더라도 비정상 케이스에 포함해야함

11. 비정상 : get_current_time_raw 케이스
- 예시코드
using Tizen.TV.Application.Utility
uint time = TimeUtil.CurrentTimeRaw;

- 이유
Tizen.TV.Application.Utility namespace의 TimeUtil 클래스의 CurrentTime 게터에서 Interop.Internal.get_current_time_raw(); 를 호출함으로써 dotnet-native-bridge를 불러오게 되어 있다.
이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.get_current_time_raw() 을 직접 호출하더라도 비정상 케이스에 포함해야함

12. 정상 : get_clock_mode 케이스
- 예시코드
using Tizen.TV.Service.CNMedia
string clockMode = TimeManager.GetClockModeType();

- 이유
TimeManager 클래스의 GetClockModeType() 함수 안에 TimeUtil.ClockModeType clockMode = TimeUtil.ClockMode 로 게터를 호출함 ClockMode 게터안에는 get_clock_mode가 있어 dotnet-native-bridge를 불러오게 되어 있다
이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.get_clock_mode() 을 직접 호출하더라도 정상 케이스에 포함해야함

13. 정상 : set_clock_mode 케이스
- 예시코드
using Tizen.TV.Application.Utility;
TimeUtil.ClockMode = TimeUtil.ClockModeType.Manual;

- 이유
TimeUtil의 ClockMode 세터안에는 set_clock_mode가 있어 dotnet-native-bridge를 불러오게 되어 있다, 이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.set_clock_mode() 을 직접 호출하더라도 정상 케이스에 포함해야함

14. 정상 : get_time_zone 케이스
- 예시코드
using Tizen.TV.Application.Utility;
Assert.DoesNotThrow(() => timeZone = TimeUtil.TimeZone, "sholdn't throw an exception");

- 이유
TimeUtil의 클래스의  TimeZone 게터안에는 get_time_zone 있어 dotnet-native-bridge를 불러오게 되어 있다, 이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.get_time_zone() 을 직접 호출하더라도 정상 케이스에 포함해야함

15. 정상 : set_time_zone 케이스
- 예시코드
using Tizen.TV.Application.Utility;
TimeUtil.TimeZone = value("Seoul")

- 이유
TimeUtil의 클래스의  TimeZone 세터안에는 set_time_zone 있어 dotnet-native-bridge를 불러오게 되어 있다, 이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.set_time_zone() 을 직접 호출하더라도 정상 케이스에 포함해야함

16. 정상 : flag_time_zone_supoort() 케이스
- 예시코드
using Tizen.TV.Application.Utility;
bool ret = TimeUtil.SupportTimeZone;

- 이유
TimeUtil의 클래스의  SupportTimeZone 세터안에는 flag_time_zone_supoort 있어 dotnet-native-bridge를 불러오게 되어 있다, 이 예시 처럼 간접적으로 호출하는 것 외에도 Interop.Internal.flag_time_zone_supoort() 을 직접 호출하더라도 정상 케이스에 포함해야함
