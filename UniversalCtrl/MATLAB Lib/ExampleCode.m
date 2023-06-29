%% Example code for using HV Control
% Require the code 'HVControl.m' stored in the added path

% Parameter needed for both DC and vibration output:
voltageLevel = 100; % Percentage of voltage level (%)

% Parameter needed for vibration output only:
frequency = 20; % Vibration frequency (Hz)
vibrationTime = 1000; % Vibration duration (ms)
vibrationIntervalTime = 500; % Vibration interval (ms)

% Parameter needed for DC output only:
chargeTime = 200; % DC output charging time  (ms)
dischargeTime = 500; % DC output discharging time (ms), must be longer 
                       % than the charging time in order to fully discharge 
                       % the actuator

%% Must be executed before sending any command to the HV controller
obj0 = HVControl(); % (Click the function name and press F1 for help)

%% Example code segment to output vibrations (Sinewave/PulseTrain)
obj0.VibrationSetting(voltageLevel, frequency, vibrationTime)

repeatNumber = 2;

for i = 1:repeatNumber
    obj0.OutputSinewave(); % Output sinusodal vibrations
    pause((vibrationTime + vibrationIntervalTime)/1000); % Must pause long 
                                % enough for current output to be finished
end

for i = 1:repeatNumber
    obj0.OutputPulseTrain(); % Output pulse train vibrations
    pause((vibrationTime + vibrationIntervalTime)/1000); % Must pause long 
                                % enough for current output to be finished
end

%% Example code segment to output DC force
obj0.DCSetting(voltageLevel, chargeTime, dischargeTime);

repeatNumber = 3;

for i = 1:repeatNumber
    obj0.OutputDC();
    pause((chargeTime + dischargeTime)/1000); % Must pause long enough for 
                                           % current output to be finished
end

%% Example code segment to charge and discharge actuator by event
% [WARNING] Besure you know how the actuator works under high-voltage
% charging and discharging. Over charging may cause electrical shock or 
% even health-risks to the user touching the actuator! 
obj0.DCSetting(voltageLevel, chargeTime, dischargeTime);

prompt = "Press ENTER:";

input(prompt);
obj0.Charge();

input(prompt);
obj0.Discharge();

%% Must be executed at the end of the program to release the server
clear obj0; % Must be called to release the server at the end, otherwise 
            % new connection to the server is impossible.