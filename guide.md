If you want Windows to falsely display a higher physical RAM number (e.g., making a 16 GB PC explicitly say "32 GB" in the Windows About page), it cannot be done through legitimate system settings like Virtual Memory.
To force Windows to display a fake RAM amount, you have to use Registry Spoofing.
Disclaimer: This is a visual illusion. It only changes the text displayed on the screen; it does not give your computer more memory or improve performance. If your PC tries to use more than its real physical RAM, it will crash.
Here is how people trick the Windows interface into showing increased RAM:

Step-by-Step: The Registry Spoofing Trick

This method forces Windows to pull a custom description text for your system properties instead of reading the hardware directly.
1. Press Windows Key + R, type regedit, and press Enter to open the Registry Editor.
2. Navigate to the following folder path:
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\SystemInformation
3. Look for a value named BiosVersion or SystemBiosVersion.
4. Double-click it, and add your desired text to the end of the existing value data (for example, adding | 32.0 GB RAM).
5. For a more thorough fake (to alter older system info windows), people navigate to:
HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System\CentralProcessor\0
6. They modify the ProcessorNameString key. By editing this text, they can rewrite the CPU line to say whatever they want, such as: Intel Core i7 @ 3.50GHz (32GB RAM installed).

The Cheat: Using a Fake Driver / Script

More sophisticated scammers use custom batch scripts or malicious .inf hardware drivers to hijack the WMI (Windows Management Instrumentation) service.
• WMI is the background service that tells Windows what hardware is plugged in.
• By injecting a script that intercepts WMI queries, a user can trick both the Settings App and Task Manager into displaying a fake total capacity (like 32 GB or 64 GB) at a glance.

How to Tell it's a Trick (Why it Fails)

Even if someone perfectly spoofs the Windows interface, the illusion instantly falls apart under any real diagnostic test:
• Task Manager Live Graph: While the text might say "32 GB", the memory composition graph will still physically top out and throttle the system the moment it hits your real physical limit (e.g., 16 GB).
• Direct Hardware Queries: If you open Command Prompt and run wmic memorychip get capacity, Windows queries the motherboard's physical slots directly, bypassing the visual registry edits entirely to show the true capacity.
Are you trying to test a friend or student with a prank configuration, or are you trying to verify if a second-hand PC you are looking to buy has been altered with a fake specs layout? Let me know the context so I can show you how to lock down or verify the system!
