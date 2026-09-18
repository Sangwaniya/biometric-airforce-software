using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;

namespace eSSLBridgeService
{
    class Program
    {
        // Standalone SDK COM wrapper for eSSL Multi-Biometric Terminals
        private static zkemkeeper.CZKEMClass axCZKEM1 = new zkemkeeper.CZKEMClass();
        private static bool isConnected = false;
        private static string serverApiUrl = "http://127.0.0.1:8000/api/essl/punch";

        static void Main(string[] args)
        {
            Console.WriteLine("=========================================================");
            Console.WriteLine("  eSSL Multi-Biometric Hardware Gateway (All-in-One SDK) ");
            Console.WriteLine("  Face Recognition + Fingerprint + RFID Card Interop     ");
            Console.WriteLine("=========================================================");

            string deviceIp = args.Length > 0 ? args[0] : "192.168.1.201";
            int devicePort = args.Length > 1 ? int.Parse(args[1]) : 4370;

            Console.WriteLine(string.Format("[INFO] Connecting to eSSL multi-biometric terminal at {0}:{1}...", deviceIp, devicePort));

            try
            {
                axCZKEM1.PullMode = 1;
                isConnected = axCZKEM1.Connect_Net(deviceIp, devicePort);

                if (isConnected)
                {
                    Console.WriteLine("[SUCCESS] Connected to eSSL terminal (uFace / SilkBio / MB series)!");
                    int machineNumber = 1;
                    
                    // Register all real-time events (65535 = Face, Finger, Card, Door)
                    if (axCZKEM1.RegEvent(machineNumber, 65535))
                    {
                        Console.WriteLine("[INFO] Real-time hardware punch event listener registered.");
                    }

                    // Attach event handlers
                    axCZKEM1.OnAttTransactionEx += AxCZKEM1_OnAttTransactionEx;

                    Console.WriteLine("[RUNNING] eSSL Bridge is actively listening for Face/Finger/Card punches. Press CTRL+C to exit.");
                    
                    while (true)
                    {
                        Thread.Sleep(1000);
                    }
                }
                else
                {
                    int errorCode = 0;
                    axCZKEM1.GetLastError(ref errorCode);
                    Console.WriteLine(string.Format("[WARN] Could not connect to physical device at {0}:{1} (ErrorCode: {2}).", deviceIp, devicePort, errorCode));
                    Console.WriteLine("[INFO] Running in simulated stand-by mode for local core server...");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(string.Format("[ERROR] eSSL Bridge Exception: {0}", ex.Message));
            }
        }

        private static void AxCZKEM1_OnAttTransactionEx(
            string sEnrollNumber,
            int iIsInValid,
            int iAttState,
            int iVerifyMethod,
            int iYear,
            int iMonth,
            int iDay,
            int iHour,
            int iMinute,
            int iSecond,
            int iWorkCode)
        {
            string punchTime = string.Format("{0:D4}-{1:D2}-{2:D2} {3:D2}:{4:D2}:{5:D2}", iYear, iMonth, iDay, iHour, iMinute, iSecond);
            Console.WriteLine(string.Format("[EVENT] eSSL Punch: User={0}, Method={1} (Face/Finger/Card), Time={2}", sEnrollNumber, iVerifyMethod, punchTime));

            // Post to Central Core Server
            try
            {
                var request = (HttpWebRequest)WebRequest.Create(serverApiUrl);
                request.Method = "POST";
                request.ContentType = "application/json";

                string jsonPayload = string.Format("{{\"device_user_pin\":\"{0}\",\"verify_mode\":{1},\"in_out_mode\":{2},\"timestamp\":\"{3}\"}}",
                    sEnrollNumber, iVerifyMethod, iAttState, punchTime);
                byte[] data = Encoding.UTF8.GetBytes(jsonPayload);
                request.ContentLength = data.Length;

                using (var stream = request.GetRequestStream())
                {
                    stream.Write(data, 0, data.Length);
                }

                using (var response = (HttpWebResponse)request.GetResponse())
                {
                    Console.WriteLine(string.Format("[DISPATCH] Server response status: {0}", response.StatusCode));
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(string.Format("[WARN] Failed to forward punch to local core server: {0}", ex.Message));
            }
        }
    }
}
