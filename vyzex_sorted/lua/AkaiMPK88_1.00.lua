function remote_init()
	local items={
		{name="Keyboard", input="keyboard"},
		{name="Channel Pressure", input="value", min=0, max=127},
		{name="Mod Wheel", input="value", min=0, max=127},
		{name="Pitch Bend", input="value", min=0, max=16384},
		{name="Expression", input="value", min=0, max=127},
		{name="Damper Pedal", input="value", min=0, max=127},

		{name="Fader 1", input="value", min=0, max=127},
		{name="Fader 2", input="value", min=0, max=127},
		{name="Fader 3", input="value", min=0, max=127},
		{name="Fader 4", input="value", min=0, max=127},
		{name="Fader 5", input="value", min=0, max=127},
		{name="Fader 6", input="value", min=0, max=127},
		{name="Fader 7", input="value", min=0, max=127},
		{name="Fader 8", input="value", min=0, max=127},

		{name="Fader 9", input="value", min=0, max=127},
		{name="Fader 10", input="value", min=0, max=127},
		{name="Fader 11", input="value", min=0, max=127},
		{name="Fader 12", input="value", min=0, max=127},
		{name="Fader 13", input="value", min=0, max=127},
		{name="Fader 14", input="value", min=0, max=127},
		{name="Fader 15", input="value", min=0, max=127},
		{name="Fader 16", input="value", min=0, max=127},

		{name="Fader 17", input="value", min=0, max=127},
		{name="Fader 18", input="value", min=0, max=127},
		{name="Fader 19", input="value", min=0, max=127},
		{name="Fader 20", input="value", min=0, max=127},
		{name="Fader 21", input="value", min=0, max=127},
		{name="Fader 22", input="value", min=0, max=127},
		{name="Fader 23", input="value", min=0, max=127},
		{name="Fader 24", input="value", min=0, max=127},

		{name="Knob 1", input="value", min=0, max=127},
		{name="Knob 2", input="value", min=0, max=127},
		{name="Knob 3", input="value", min=0, max=127},
		{name="Knob 4", input="value", min=0, max=127},
		{name="Knob 5", input="value", min=0, max=127},
		{name="Knob 6", input="value", min=0, max=127},
		{name="Knob 7", input="value", min=0, max=127},
		{name="Knob 8", input="value", min=0, max=127},

		{name="Knob 9", input="value", min=0, max=127},
		{name="Knob 10", input="value", min=0, max=127},
		{name="Knob 11", input="value", min=0, max=127},
		{name="Knob 12", input="value", min=0, max=127},
		{name="Knob 13", input="value", min=0, max=127},
		{name="Knob 14", input="value", min=0, max=127},
		{name="Knob 15", input="value", min=0, max=127},
		{name="Knob 16", input="value", min=0, max=127},

		{name="Knob 17", input="value", min=0, max=127},
		{name="Knob 18", input="value", min=0, max=127},
		{name="Knob 19", input="value", min=0, max=127},
		{name="Knob 20", input="value", min=0, max=127},
		{name="Knob 21", input="value", min=0, max=127},
		{name="Knob 22", input="value", min=0, max=127},
		{name="Knob 23", input="value", min=0, max=127},
		{name="Knob 24", input="value", min=0, max=127},
				
		{name="Switch 1", input="value", min=0, max=127},
		{name="Switch 2", input="value", min=0, max=127},
		{name="Switch 3", input="value", min=0, max=127},
		{name="Switch 4", input="value", min=0, max=127},
		{name="Switch 5", input="value", min=0, max=127},
		{name="Switch 6", input="value", min=0, max=127},
		{name="Switch 7", input="value", min=0, max=127},
		{name="Switch 8", input="value", min=0, max=127},

		{name="Switch 9", input="value", min=0, max=127},
		{name="Switch 10", input="value", min=0, max=127},
		{name="Switch 11", input="value", min=0, max=127},
		{name="Switch 12", input="value", min=0, max=127},
		{name="Switch 13", input="value", min=0, max=127},
		{name="Switch 14", input="value", min=0, max=127},
		{name="Switch 15", input="value", min=0, max=127},
		{name="Switch 16", input="value", min=0, max=127},

		{name="Switch 17", input="value", min=0, max=127},
		{name="Switch 18", input="value", min=0, max=127},
		{name="Switch 19", input="value", min=0, max=127},
		{name="Switch 20", input="value", min=0, max=127},
		{name="Switch 21", input="value", min=0, max=127},
		{name="Switch 22", input="value", min=0, max=127},
		{name="Switch 23", input="value", min=0, max=127},
		{name="Switch 24", input="value", min=0, max=127},
		
		{name="Pad D1", input="button"},
		{name="Pad D2", input="button"},
		{name="Pad D3", input="button"},
		{name="Pad D4", input="button"},
		{name="Pad D5", input="button"},
		{name="Pad D6", input="button"},
		{name="Pad D7", input="button"},
		{name="Pad D8", input="button"},
		{name="Pad D9", input="button"},
		{name="Pad D10", input="button"},
		{name="Pad D11", input="button"},
		{name="Pad D12", input="button"},
		{name="Pad D13", input="button"},
		{name="Pad D14", input="button"},
		{name="Pad D15", input="button"},
		{name="Pad D16", input="button"},

		{name="Rewind", input="button"},
		{name="Fast Forward", input="button"},
		{name="Stop", input="button"},
		{name="Play", input="button"},
		{name="Record", input="button"},

			}
	remote.define_items(items)

	local inputs={
		{pattern="b0 0C xx", name="Fader 1"},
		{pattern="b0 0D xx", name="Fader 2"},
		{pattern="b0 0E xx", name="Fader 3"},
		{pattern="b0 0F xx", name="Fader 4"},
		{pattern="b0 10 xx", name="Fader 5"},
		{pattern="b0 11 xx", name="Fader 6"},
		{pattern="b0 12 xx", name="Fader 7"},
		{pattern="b0 13 xx", name="Fader 8"},

		{pattern="b1 0C xx", name="Fader 9"},
		{pattern="b1 0D xx", name="Fader 10"},
		{pattern="b1 0E xx", name="Fader 11"},
		{pattern="b1 0F xx", name="Fader 12"},
		{pattern="b1 10 xx", name="Fader 13"},
		{pattern="b1 11 xx", name="Fader 14"},
		{pattern="b1 12 xx", name="Fader 15"},
		{pattern="b1 13 xx", name="Fader 16"},
		
		{pattern="b2 0C xx", name="Fader 17"},
		{pattern="b2 0D xx", name="Fader 18"},
		{pattern="b2 0E xx", name="Fader 19"},
		{pattern="b2 0F xx", name="Fader 20"},
		{pattern="b2 10 xx", name="Fader 21"},
		{pattern="b2 11 xx", name="Fader 22"},
		{pattern="b2 12 xx", name="Fader 23"},
		{pattern="b2 13 xx", name="Fader 24"},

		{pattern="b0 02 xx", name="Knob 1"},
		{pattern="b0 03 xx", name="Knob 2"},
		{pattern="b0 04 xx", name="Knob 3"},
		{pattern="b0 05 xx", name="Knob 4"},
		{pattern="b0 06 xx", name="Knob 5"},
		{pattern="b0 07 xx", name="Knob 6"},
		{pattern="b0 08 xx", name="Knob 7"},
		{pattern="b0 09 xx", name="Knob 8"},

		{pattern="b1 02 xx", name="Knob 9"},
		{pattern="b1 03 xx", name="Knob 10"},
		{pattern="b1 04 xx", name="Knob 11"},
		{pattern="b1 05 xx", name="Knob 12"},
		{pattern="b1 06 xx", name="Knob 13"},
		{pattern="b1 07 xx", name="Knob 14"},
		{pattern="b1 08 xx", name="Knob 15"},
		{pattern="b1 09 xx", name="Knob 16"},
		
		{pattern="b2 02 xx", name="Knob 17"},
		{pattern="b2 03 xx", name="Knob 18"},
		{pattern="b2 04 xx", name="Knob 19"},
		{pattern="b2 05 xx", name="Knob 20"},
		{pattern="b2 06 xx", name="Knob 21"},
		{pattern="b2 07 xx", name="Knob 22"},
		{pattern="b2 08 xx", name="Knob 23"},
		{pattern="b2 09 xx", name="Knob 24"},

		{pattern="b0 15 xx", name="Switch 1"},
		{pattern="b0 16 xx", name="Switch 2"},
		{pattern="b0 17 xx", name="Switch 3"},
		{pattern="b0 18 xx", name="Switch 4"},
		{pattern="b0 19 xx", name="Switch 5"},
		{pattern="b0 1A xx", name="Switch 6"},
		{pattern="b0 1B xx", name="Switch 7"},
		{pattern="b0 1C xx", name="Switch 8"},

		{pattern="b1 15 xx", name="Switch 9"},
		{pattern="b1 16 xx", name="Switch 10"},
		{pattern="b1 17 xx", name="Switch 11"},
		{pattern="b1 18 xx", name="Switch 12"},
		{pattern="b1 19 xx", name="Switch 13"},
		{pattern="b1 1A xx", name="Switch 14"},
		{pattern="b1 1B xx", name="Switch 15"},
		{pattern="b1 1C xx", name="Switch 16"},
		
		{pattern="b2 15 xx", name="Switch 17"},
		{pattern="b2 16 xx", name="Switch 18"},
		{pattern="b2 17 xx", name="Switch 19"},
		{pattern="b2 18 xx", name="Switch 20"},
		{pattern="b2 19 xx", name="Switch 21"},
		{pattern="b2 1A xx", name="Switch 22"},
		{pattern="b2 1B xx", name="Switch 23"},
		{pattern="b2 1C xx", name="Switch 24"},

		{pattern="9F 00 ??", name="Pad D1", value="1"},
		{pattern="9F 01 ??", name="Pad D2", value="1"},
		{pattern="9F 02 ??", name="Pad D3", value="1"},
		{pattern="9F 03 ??", name="Pad D4", value="1"},
		{pattern="9F 04 ??", name="Pad D5", value="1"},
		{pattern="9F 05 ??", name="Pad D6", value="1"},
		{pattern="9F 06 ??", name="Pad D7", value="1"},
		{pattern="9F 07 ??", name="Pad D8", value="1"},
		{pattern="9F 08 ??", name="Pad D9", value="1"},
		{pattern="9F 09 ??", name="Pad D10", value="1"},
		{pattern="9F 0A ??", name="Pad D11", value="1"},
		{pattern="9F 0B ??", name="Pad D12", value="1"},
		{pattern="9F 0C ??", name="Pad D13", value="1"},
		{pattern="9F 0D ??", name="Pad D14", value="1"},
		{pattern="9F 0E ??", name="Pad D15", value="1"},
		{pattern="9F 0F ??", name="Pad D16", value="1"},

		{pattern="e? xx yy", name="Pitch Bend", value="y*128 + x"},
		{pattern="b0 01 xx", name="Mod Wheel"},
		{pattern="b0 0b xx", name="Expression"},
		{pattern="b0 40 xx", name="Damper Pedal"},
		{pattern="d0 xx", name="Channel Pressure"},

		{pattern="80 xx yy", name="Keyboard", value="0", note="x", velocity="64"},
		
		{pattern="90 xx 00", name="Keyboard", value="0", note="x", velocity="64"},
		{pattern="<100x>0 yy zz", name="Keyboard"},

		{pattern="F0 7F 7F 06 05 F7", name="Rewind", value="1"},
		{pattern="F0 7F 7F 06 04 F7", name="Fast Forward", value="1"},
		{pattern="F0 7F 7F 06 01 F7", name="Stop", value="1"},
		{pattern="F0 7F 7F 06 02 F7", name="Play", value="1"},
		{pattern="F0 7F 7F 06 06 F7", name="Record", value="1"},
	

	}
	remote.define_auto_inputs(inputs)
end



function remote_probe()

	local controlRequest="F0 7E 7F 06 01 F7"

	local controlResponse="F0 7E 00 06 02 47 71 00 19 00 ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? F7"
return {
		request=controlRequest,
		response=controlResponse
	}
end


