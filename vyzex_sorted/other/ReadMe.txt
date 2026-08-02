---------------------------------------------
------------    Vyzex MPK88/61  -------------
-----            Version 1.00         -------
---------------------------------------------

*** VERSION 1.00 : RC 1 ***
    Built June 16, 2009
    
1. Release notes:

   Initial Release
      

2. Installing to Windows 2000

   **** NOTE: THE USB MIDI DRIVER IS NOT SUPPORTED ON WINDOWS 2000: DO NOT CONNECT USB!!! ****
   ** Computers running Windows 2000 will blue screen crash if MPK88 or MPK61 is connected  ** 
   **     via USB. Instead, use a 3rd party MIDI interface connected to the MPK MIDI ports. ** 
   *******************************************************************************************              

   In order to run Vyzex MPK88-61 in windows 2000 there is some additional setup
   work required. Inside the Vyzex MPK25 installation there will be two folders:
   
   Microsoft.VC80.CRT
   Microsoft.VC80.MFC

   The contents of these two folders must be copied to the Windows\System32
   folder.

   In addition, you need to install the gdiplus.dll from Microsoft. Go to

   http://www.microsoft.com/downloads/details.aspx?familyid=6a63ab9c-df12-4d41-933c-be590feaa05a&displaylang=en
   
   and download GDIPlus. Expand the file into the same Windows\System32 folder.

   You should now be ready to run Vyzex MPK88/61, but you will ned to use 
   a 3rd party MIDI interface connected to the MPK MIDI ports.
   
   NOTE: Psicraft Designs Inc. and/or Akai Professional cannot be responsible for any issues caused by user modifications 
   to your windows installation: Do so at your own risk.
   