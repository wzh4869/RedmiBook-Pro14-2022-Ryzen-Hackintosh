DefinitionBlock ("", "SSDT", 2, "RMBK", "TPD0", 0x00000001)
{
    External (\THPD, FieldUnitObj)
    External (\_SB.I2CA.TPD0, DeviceObj)
    External (\_SB.I2CA.TPD0.XSTA, MethodObj)

    Scope (\_SB.I2CA.TPD0)
    {
        Method (_STA, 0, NotSerialized)
        {
            // The firmware hides this device unless TPOS identifies Windows 8+.
            If (_OSI ("Darwin"))
            {
                If (THPD == 0x15)
                {
                    Return (0x0F)
                }
                Return (Zero)
            }
            Return (XSTA ())
        }
    }
}
