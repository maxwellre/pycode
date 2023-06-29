%% Class: WiFi Remote Control of High Voltage (HV) Controller
classdef HVControl < handle
    % This class handles the communication with a remote HV controller via
    % WiFi. HV output can be controlled by sending commands.
    % ---------------------------------------------------------------------
    % Author: Yitian Shao (yitian.shao@tu-dresden.de)
    % Created on 30.06.2023
    %% Properties
    properties % [public] -------------------------------------------------
        ServerAddress; % Address of the server (HV controller)
        ServerPort; % Port of the server (HV controller)
        IsConnected; % Connection status of the server (HV controller)
        IsIdle; % Can only send a command when the HV controller is 'Idle'
    end

    properties(GetAccess = private) % [private] --------------------------- 
        client0; % [private] Client object connecting to the controller
    end

    methods % Methods -----------------------------------------------------
        %% Constructor Function: Initialize WiFi Connection with the HV controller  
        function obj = HVControl()
        % The constructor must be executed at the beginning. It will try to initialize a connection with a remote HV controller via WiFi. Connection must be established before the 60 s timeout.
        % Output:
        % 1. 'obj' - an instance of the 'HVControl' class

        % ''' Configuration of WiFi connection '''
        obj.ServerAddress = "192.168.4.1";  % The server's hostname or IP
        % address (Need not change)
        obj.ServerPort = 80; % The port used by the server (Need not change)
        
        obj.client0 = tcpclient(obj.ServerAddress,obj.ServerPort,...
            "ConnectTimeout",60);
        
        obj.IsConnected = false;
        obj.IsIdle = false;
        
        while ~obj.IsConnected
            write(obj.client0,"vrheadset","string");
        
            for i = 1:100
                controllerResponse = read(obj.client0,...
                    obj.client0.NumBytesAvailable,"string");
                if(~isempty(controllerResponse) &&...
                controllerResponse == "high-voltage-controller-is-ready")
                    obj.IsConnected = true;
                    fprintf("Successful connection to high voltage controller\n");
                    obj.IsIdle = true;
                    return;
                end
                fprintf("Waiting ... %d\n", i);
                pause(0.5);
            end
            fprintf("No response from the HV controller: Retrying...\n");
        end
        end

        %% Function: Send Customized Command to the HV controller ---------
        function Command(obj, text)
        % For general command, using predefined command coding rather than sending a customized command through this function. 
        % Input: 
        % 1. 'text' - a string or a char encoding the command; A char for 
        % fast command while a string for slow but detailed setting. If the
        % command cannot be decoded by the HV controller, no response will 
        % be returned from the HV controller.

            if (~obj.IsIdle)
                fprintf("HV controller is busy: Failed to send the command\n");
                return;
            end

            obj.IsIdle = false;

            % ''' Acknowledge table: find the correct answer string '''
            if (text == 's') % Use char for fast menu selection command
                acknowledgeStr = "ready-to-change";
            elseif (~ischar(text)) % Use string for slow but informative 
                                      % setting command
                acknowledgeStr = "setting-changed";
            else
                acknowledgeStr = "command-received";
            end
            
            write(obj.client0,text,"string");

            for i = 1:1000000
                controllerResponse = read(obj.client0,...
                    obj.client0.NumBytesAvailable,"string");
                if(~isempty(controllerResponse) &&...
                        contains(controllerResponse,acknowledgeStr))
                    obj.IsIdle = true;
                    return;
                end
            end
            fprintf("Failed to send the command: %s\n", text);
            end

        %% Function: Send Encoded Command to output DC voltage [1]
        function OutputDC(obj)
        % Command the controller to output DC high voltage with predefined voltage level, charge and discharge time. Predefine the parameters using 'DCSetting'.
        % (No input)
            obj.Command('l');
        end

        %% Function: Send Encoded Command to output Pulse Train [2]
        function OutputPulseTrain(obj)
        % Command the controller to output a pulse train with predefined voltage level and frequency. Predefine the parameters using 'VibrationSetting'.
        % (No input)
            obj.Command('w');
        end

        %% Function: Send Encoded Command to output Sinewave [3]
        function OutputSinewave(obj)
        % Command the controller to output sinusoidal waves with predefined voltage level and frequency. Predefine the parameters using 'VibrationSetting'. 
        % (No input)
            obj.Command('x');
        end

        %% Function: Send Encoded Command to charge the actuator [4]
        function Charge(obj)
        % Command the controller to charge the actuator with predefined voltage level and charge time. Predefine the parameters using 'DCSetting'. [WARNING] Besure you know how to use the 'Charge' and 'Discharge' command properly, since an overly charged actuator may result in electrical shock and even consequential health-risks! 
        % [WARNING] Avoid using 'Charge' command unless you know what you
        % are doing.
        % (No input)
            obj.Command('n');
        end

        %% Function: Send Encoded Command to discharge the actuator [5]
        function Discharge(obj)
        % Command the controller to discharge the actuator with predefined voltage level and discharge time. Predefine the parameters using 'DCSetting'.
        % (No input)
            obj.Command('f');
        end

        %% Function: Send Encoded Commands to set vibration parameters [6]
        function VibrationSetting(obj, voltageLevel, frequency,...
                vibrationTime)
        % Set the parameters for controlling vibration output.
        % Inputs:
        % 1. 'voltageLevel' - an integer between 0 and 100 (%), controlling
        %                     the output voltage level of the HV controller
        % 2. 'frequency' - an integer between 0 and 1000 (Hz), controlling
        %                  the frequency of the vibration, in the form of a
        %                  sinewave or a pulse train
        % 3. 'vibrationTime' - an integer between 0 and 4000 (ms),
        %                      controlling the total vibration time
            if(isnumeric(voltageLevel) && isnumeric(frequency) &&...
                    isnumeric(vibrationTime))
                obj.Command('s');
                obj.Command(sprintf("Vo=%03d-Fr=%03d-Ti=%04d",...
                    round(voltageLevel), round(frequency),...
                    round(vibrationTime)));
            else
                fprintf("Only integers are allowed as the input for the setting")
            end
        end

        %% Function: Send Encoded Commands to set DC force parameters [7]
        function DCSetting(obj, voltageLevel, chargeTime,...
                dischargeTime)
        % Set the parameters for controlling DC (force) output.
        % Inputs:
        % 1. 'voltageLevel' - an integer between 0 and 100 (%), controlling
        %                     the output voltage level of the HV controller
        % 2. 'chargeTime' - an integer between 0 and 4000 (ms), controlling
        %                  the charge time of DC output or Charge command
        % 3. 'dischargeTime' - an integer between 0 and 4000 (ms),
        %                      controlling the discharge time of DC output 
        %                      or Charge command
            if(isnumeric(voltageLevel) && isnumeric(chargeTime) &&...
                    isnumeric(dischargeTime))
                obj.Command('s');
                obj.Command(sprintf("Vo=%03d-Ch=%04d-Di=%04d",...
                    round(voltageLevel), round(chargeTime),...
                    round(dischargeTime)));
            else
                fprintf("Only integers are allowed as the input for the setting")
            end
        end

        %% Destructor Function
        function delete(~)
            clear obj.client0;
            fprintf("HV controller disconnected\n")
        end
    %% --------------------------------------------------------------------
    end
end