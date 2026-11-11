// Processor IDs are derived from this RedmiBook's MADT (0..15).
DefinitionBlock ("", "SSDT", 2, "RMBK", "CpuPlug", 0x00000001)
{
    Scope (\_SB)
    {
        Processor (CP00, 0x00, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP01, 0x01, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP02, 0x02, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP03, 0x03, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP04, 0x04, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP05, 0x05, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP06, 0x06, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP07, 0x07, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP08, 0x08, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP09, 0x09, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP0A, 0x0A, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP0B, 0x0B, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP0C, 0x0C, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP0D, 0x0D, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP0E, 0x0E, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
        Processor (CP0F, 0x0F, Zero, Zero)
        {
            Method (_STA, 0, NotSerialized)
            {
                If (_OSI ("Darwin")) { Return (0x0F) }
                Return (Zero)
            }
        }
    }
    Method (\_SB.CP00._DSM, 4, NotSerialized)
    {
        If (Arg2 == Zero) { Return (Buffer (One) { 0x03 }) }
        Return (Package (0x02) { "plugin-type", One })
    }
}
