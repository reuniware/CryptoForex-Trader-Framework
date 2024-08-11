// This work is licensed under a Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) https://creativecommons.org/licenses/by-nc-sa/4.0/
// © LuxAlgo : Original work by LuxAlgp ; I tried to convert to MQL5... But it seems not to show the same info visually.

#property indicator_chart_window
#property indicator_buffers 2
#property indicator_color1 clrGreen
#property indicator_color2 clrRed

// Inputs
input int length = 5; // Volume Pivot Length
input int bull_ext_last = 3; // Bullish OB
input color bg_bull_css = C'22,148,0'; // Bullish OB Background Color
input color bull_css = clrGreen; // Bullish OB Color
input color bull_avg_css = C'149,152,161'; // Bullish OB Average Color
input int bear_ext_last = 3; // Bearish OB
input color bg_bear_css = C'255,17,0'; // Bearish OB Background Color
input color bear_css = clrRed; // Bearish OB Color
input color bear_avg_css = C'149,152,161'; // Bearish OB Average Color
input string line_style = "⎯⎯⎯"; // Average Line Style
input int line_width = 1; // Average Line Width
input string mitigation = "Wick"; // Mitigation Methods

// Indicator buffers
double bull_ob_buffer[];
double bear_ob_buffer[];

// Global variables
int os = 0;
double target_bull = 0.0;
double target_bear = 0.0;

// Functions
ENUM_LINE_STYLE GetLineStyle(string style) {
    if (style == "⎯⎯⎯") return STYLE_SOLID;
    else if (style == "----") return STYLE_DASH;
    else if (style == "····") return STYLE_DOT;
    return STYLE_SOLID;
}

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit() {
    SetIndexBuffer(0, bull_ob_buffer);
    SetIndexBuffer(1, bear_ob_buffer);
    
    PlotIndexSetInteger(0, PLOT_DRAW_TYPE, DRAW_LINE);
    PlotIndexSetInteger(0, PLOT_LINE_STYLE, STYLE_SOLID);
    PlotIndexSetInteger(0, PLOT_LINE_WIDTH, 2);
    PlotIndexSetInteger(0, PLOT_LINE_COLOR, clrGreen);
    
    PlotIndexSetInteger(1, PLOT_DRAW_TYPE, DRAW_LINE);
    PlotIndexSetInteger(1, PLOT_LINE_STYLE, STYLE_SOLID);
    PlotIndexSetInteger(1, PLOT_LINE_WIDTH, 2);
    PlotIndexSetInteger(1, PLOT_LINE_COLOR, clrRed);
    
    PlotIndexSetString(0, PLOT_LABEL, "Bull OB");
    PlotIndexSetString(1, PLOT_LABEL, "Bear OB");
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Custom pivot high calculation based on volume                    |
//+------------------------------------------------------------------+
double CalculatePivotHighVolume(int length, int shift) {
    double high = iHigh(NULL, 0, shift);
    double volume = iVolume(NULL, 0, shift);
    
    for (int i = 1; i <= length; i++) {
        if (iHigh(NULL, 0, shift + i) >= high || iHigh(NULL, 0, shift - i) >= high) {
            return EMPTY_VALUE; // Not a pivot high
        }
    }
    
    // Check volume criteria (e.g., volume must be above a certain threshold)
    double volumeThreshold = 1000; // Example threshold
    if (volume < volumeThreshold) {
        return EMPTY_VALUE; // Volume does not meet criteria
    }
    
    return high;
}

//+------------------------------------------------------------------+
//| OnCalculate function                                             |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total, const int prev_calculated, const datetime &time[], const double &open[], const double &high[], const double &low[], const double &close[], const long &tick_volume[], const long &volume[], const int &spread[]) {
    int begin = MathMax(length, prev_calculated);
    for (int i = begin; i < rates_total; i++) {
        double upper = iHigh(NULL, 0, iHighest(NULL, 0, MODE_HIGH, length, i - length));
        double lower = iLow(NULL, 0, iLowest(NULL, 0, MODE_LOW, length, i - length));

        if (mitigation == "Close") {
            target_bull = iLow(NULL, 0, iLowest(NULL, 0, MODE_CLOSE, length, i - length));
            target_bear = iHigh(NULL, 0, iHighest(NULL, 0, MODE_CLOSE, length, i - length));
        } else {
            target_bull = lower;
            target_bear = upper;
        }

        os = (iHigh(NULL, 0, i - length) > upper) ? 0 : (iLow(NULL, 0, i - length) < lower) ? 1 : os;

        double phv = CalculatePivotHighVolume(length, i - length);

        if (phv != EMPTY_VALUE && os == 1) {
            bull_ob_buffer[i] = iLow(NULL, 0, i - length);
            datetime time_bull = iTime(NULL, 0, i - length);
            Print("Bull OB detected at ", iLow(NULL, 0, i - length), " on bar ", i, " at time ", TimeToString(time_bull)); // Debugging
            
            // Draw Bull OB
            string objName = "BullOB_" + IntegerToString(i);
            ObjectCreate(0, objName, OBJ_RECTANGLE, 0, time_bull, iLow(NULL, 0, i - length), time_bull + PeriodSeconds() * length, iHigh(NULL, 0, i - length));
            ObjectSetInteger(0, objName, OBJPROP_COLOR, bull_css);
            ObjectSetInteger(0, objName, OBJPROP_BACK, true);
            ObjectSetInteger(0, objName, OBJPROP_STYLE, STYLE_SOLID);
            ObjectSetInteger(0, objName, OBJPROP_BGCOLOR, bg_bull_css);
            ObjectSetInteger(0, objName, OBJPROP_WIDTH, 2);
        } else {
            bull_ob_buffer[i] = EMPTY_VALUE;
        }

        if (phv != EMPTY_VALUE && os == 0) {
            bear_ob_buffer[i] = iHigh(NULL, 0, i - length);
            datetime time_bear = iTime(NULL, 0, i - length);
            Print("Bear OB detected at ", iHigh(NULL, 0, i - length), " on bar ", i, " at time ", TimeToString(time_bear)); // Debugging
            
            // Draw Bear OB
            string objName = "BearOB_" + IntegerToString(i);
            ObjectCreate(0, objName, OBJ_RECTANGLE, 0, time_bear, iLow(NULL, 0, i - length), time_bear + PeriodSeconds() * length, iHigh(NULL, 0, i - length));
            ObjectSetInteger(0, objName, OBJPROP_COLOR, bear_css);
            ObjectSetInteger(0, objName, OBJPROP_BACK, true);
            ObjectSetInteger(0, objName, OBJPROP_STYLE, STYLE_SOLID);
            ObjectSetInteger(0, objName, OBJPROP_BGCOLOR, bg_bear_css);
            ObjectSetInteger(0, objName, OBJPROP_WIDTH, 2);
        } else {
            bear_ob_buffer[i] = EMPTY_VALUE;
        }
    }
    return(rates_total);
}
