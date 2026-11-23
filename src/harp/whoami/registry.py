"""The registry of WhoAmI identifiers, generated from whoami.yml by harp-whoami generate."""

from enum import IntEnum
from types import MappingProxyType

from harp.whoami import DeviceRecord, DotnetToolApp


class WhoAmI(IntEnum):
    """The WhoAmI identifiers of the registered devices."""

    Hobgoblin = 123
    MultiPwm = 1040
    LedArray = 1088
    Synchronizer = 1104
    InputExpander = 1106
    OutputExpander = 1108
    StepperDriver = 1130
    Olfactometer = 1140
    ClockSynchronizer = 1152
    TimestampGeneratorGen3 = 1158
    CameraController = 1168
    CameraControllerGen2 = 1170
    Behavior = 1216
    VestibularH1 = 1224
    VestibularH2 = 1225
    LoadCells = 1232
    AnalogInput = 1236
    AudioSwitch = 1248
    RgbArray = 1264
    SoundCard = 1280
    CurrentDriver = 1282
    SyringePump = 1296
    LaserDriverController = 1298
    LicketySplit = 1400
    SniffDetector = 1401
    Treadmill = 1402
    Cuttlefish = 1403
    WhiteRabbit = 1404
    EnvironmentSensor = 1405
    CuttlefishFip = 1407
    deLuxDriver = 1410
    Quac = 1411
    PhotodiodeBoard = 1412
    RfidReader = 2094
    Pluma = 2110
    FastStepper = 2120


DEVICES = MappingProxyType({
    WhoAmI.Hobgoblin: DeviceRecord(whoami=WhoAmI.Hobgoblin, name='Hobgoblin', authors='harp-tech', repository_url='https://github.com/harp-tech/device.hobgoblin', project_url='https://harp-tech.org/device.hobgoblin'),
    WhoAmI.MultiPwm: DeviceRecord(whoami=WhoAmI.MultiPwm, name='MultiPwm', authors='harp-tech', repository_url='https://github.com/harp-tech/device.multipwm', project_url='https://github.com/harp-tech/device.multipwm'),
    WhoAmI.LedArray: DeviceRecord(whoami=WhoAmI.LedArray, name='LedArray', authors='harp-tech', repository_url='https://github.com/harp-tech/device.ledarray', project_url='https://github.com/harp-tech/device.ledarray'),
    WhoAmI.Synchronizer: DeviceRecord(whoami=WhoAmI.Synchronizer, name='Synchronizer', authors='harp-tech', repository_url='https://github.com/harp-tech/device.synchronizer', project_url='https://github.com/harp-tech/device.synchronizer'),
    WhoAmI.InputExpander: DeviceRecord(whoami=WhoAmI.InputExpander, name='InputExpander', authors='harp-tech', repository_url='https://github.com/harp-tech/device.inputexpander', project_url='https://github.com/harp-tech/device.inputexpander'),
    WhoAmI.OutputExpander: DeviceRecord(whoami=WhoAmI.OutputExpander, name='OutputExpander', authors='harp-tech', repository_url='https://github.com/harp-tech/device.outputexpander', project_url='https://github.com/harp-tech/device.outputexpander'),
    WhoAmI.StepperDriver: DeviceRecord(whoami=WhoAmI.StepperDriver, name='StepperDriver', authors='harp-tech', repository_url='https://github.com/harp-tech/device.stepperdriver', project_url='https://github.com/harp-tech/device.stepperdriver'),
    WhoAmI.Olfactometer: DeviceRecord(whoami=WhoAmI.Olfactometer, name='Olfactometer', authors='harp-tech', repository_url='https://github.com/harp-tech/device.olfactometer', project_url='https://github.com/harp-tech/device.olfactometer'),
    WhoAmI.ClockSynchronizer: DeviceRecord(whoami=WhoAmI.ClockSynchronizer, name='ClockSynchronizer', authors='harp-tech', repository_url='https://github.com/harp-tech/device.clocksynchronizer', project_url='https://github.com/harp-tech/device.clocksynchronizer'),
    WhoAmI.TimestampGeneratorGen3: DeviceRecord(whoami=WhoAmI.TimestampGeneratorGen3, name='TimestampGeneratorGen3', authors='harp-tech', repository_url='https://github.com/harp-tech/device.timestampgeneratorgen3', project_url='https://harp-tech.org/device.timestampgeneratorgen3'),
    WhoAmI.CameraController: DeviceRecord(whoami=WhoAmI.CameraController, name='CameraController', authors='harp-tech', repository_url='https://github.com/harp-tech/device.cameracontroller', project_url='https://github.com/harp-tech/device.cameracontroller'),
    WhoAmI.CameraControllerGen2: DeviceRecord(whoami=WhoAmI.CameraControllerGen2, name='CameraControllerGen2', authors='harp-tech', repository_url='https://github.com/harp-tech/device.cameracontrollergen2', project_url='https://github.com/harp-tech/device.cameracontrollergen2'),
    WhoAmI.Behavior: DeviceRecord(whoami=WhoAmI.Behavior, name='Behavior', authors='harp-tech', repository_url='https://github.com/harp-tech/device.behavior', project_url='https://harp-tech.org/device.behavior', app=DotnetToolApp(package='Harp.Behavior.App')),
    WhoAmI.VestibularH1: DeviceRecord(whoami=WhoAmI.VestibularH1, name='VestibularH1', authors='harp-tech', repository_url='https://github.com/harp-tech/device.vestibularH1', project_url='https://github.com/harp-tech/device.vestibularH1'),
    WhoAmI.VestibularH2: DeviceRecord(whoami=WhoAmI.VestibularH2, name='VestibularH2', authors='harp-tech', repository_url='https://github.com/harp-tech/device.vestibularH2', project_url='https://github.com/harp-tech/device.vestibularH2'),
    WhoAmI.LoadCells: DeviceRecord(whoami=WhoAmI.LoadCells, name='LoadCells', authors='harp-tech', repository_url='https://github.com/harp-tech/device.loadcells', project_url='https://github.com/harp-tech/device.loadcells'),
    WhoAmI.AnalogInput: DeviceRecord(whoami=WhoAmI.AnalogInput, name='AnalogInput', authors='harp-tech', repository_url='https://github.com/harp-tech/device.analoginput', project_url='https://github.com/harp-tech/device.analoginput'),
    WhoAmI.AudioSwitch: DeviceRecord(whoami=WhoAmI.AudioSwitch, name='AudioSwitch', authors='harp-tech', repository_url='https://github.com/harp-tech/device.audioswitch', project_url='https://github.com/harp-tech/device.audioswitch'),
    WhoAmI.RgbArray: DeviceRecord(whoami=WhoAmI.RgbArray, name='RgbArray', authors='harp-tech', repository_url='https://github.com/harp-tech/device.rgbarray', project_url='https://github.com/harp-tech/device.rgbarray'),
    WhoAmI.SoundCard: DeviceRecord(whoami=WhoAmI.SoundCard, name='SoundCard', authors='harp-tech', repository_url='https://github.com/harp-tech/device.soundcard', project_url='https://harp-tech.org/device.soundcard', app=DotnetToolApp(package='Harp.SoundCard.App')),
    WhoAmI.CurrentDriver: DeviceRecord(whoami=WhoAmI.CurrentDriver, name='CurrentDriver', authors='Champalimaud Foundation', repository_url='https://github.com/fchampalimaud/device.currentdriver', project_url='https://github.com/fchampalimaud/device.currentdriver'),
    WhoAmI.SyringePump: DeviceRecord(whoami=WhoAmI.SyringePump, name='SyringePump', authors='harp-tech', repository_url='https://github.com/harp-tech/device.syringepump', project_url='https://github.com/harp-tech/device.syringepump'),
    WhoAmI.LaserDriverController: DeviceRecord(whoami=WhoAmI.LaserDriverController, name='LaserDriverController', authors='Champalimaud Foundation', repository_url='https://github.com/fchampalimaud/device.laserdrivercontroller', project_url='https://github.com/fchampalimaud/device.laserdrivercontroller'),
    WhoAmI.LicketySplit: DeviceRecord(whoami=WhoAmI.LicketySplit, name='LicketySplit', authors='Allen Institute', repository_url='https://github.com/AllenNeuralDynamics/harp.device.lickety-split', project_url='https://github.com/AllenNeuralDynamics/harp.device.lickety-split'),
    WhoAmI.SniffDetector: DeviceRecord(whoami=WhoAmI.SniffDetector, name='SniffDetector', authors='Allen Institute', repository_url='https://github.com/AllenNeuralDynamics/harp.device.sniff-detector', project_url='https://github.com/AllenNeuralDynamics/harp.device.sniff-detector'),
    WhoAmI.Treadmill: DeviceRecord(whoami=WhoAmI.Treadmill, name='Treadmill', authors='Allen Institute', repository_url='https://github.com/AllenNeuralDynamics/harp.device.treadmill-driver', project_url='https://github.com/AllenNeuralDynamics/harp.device.treadmill-driver'),
    WhoAmI.Cuttlefish: DeviceRecord(whoami=WhoAmI.Cuttlefish, name='Cuttlefish', authors='Allen Institute', repository_url='https://github.com/AllenNeuralDynamics/harp.device.cuttlefish', project_url='https://github.com/AllenNeuralDynamics/harp.device.cuttlefish'),
    WhoAmI.WhiteRabbit: DeviceRecord(whoami=WhoAmI.WhiteRabbit, name='WhiteRabbit', authors='Allen Institute', repository_url='https://github.com/AllenNeuralDynamics/harp.device.white-rabbit', project_url='https://github.com/AllenNeuralDynamics/harp.device.white-rabbit'),
    WhoAmI.EnvironmentSensor: DeviceRecord(whoami=WhoAmI.EnvironmentSensor, name='EnvironmentSensor', authors='Allen Institute', repository_url='https://github.com/AllenNeuralDynamics/harp.device.environment-sensor', project_url='https://github.com/AllenNeuralDynamics/harp.device.environment-sensor'),
    WhoAmI.CuttlefishFip: DeviceRecord(whoami=WhoAmI.CuttlefishFip, name='CuttlefishFip', authors='Allen Institute', repository_url='https://github.com/AllenNeuralDynamics/harp.device.cuttlefish-fip', project_url='https://github.com/AllenNeuralDynamics/harp.device.cuttlefish-fip'),
    WhoAmI.deLuxDriver: DeviceRecord(whoami=WhoAmI.deLuxDriver, name='deLuxDriver', authors='Allen Institute', repository_url='https://github.com/AllenNeuralDynamics/harp.device.delux-driver', project_url='https://github.com/AllenNeuralDynamics/harp.device.delux-driver'),
    WhoAmI.Quac: DeviceRecord(whoami=WhoAmI.Quac, name='Quac', authors='Allen Institute', repository_url='https://github.com/AllenNeuralDynamics/harp.device.quac', project_url='https://github.com/AllenNeuralDynamics/harp.device.quac'),
    WhoAmI.PhotodiodeBoard: DeviceRecord(whoami=WhoAmI.PhotodiodeBoard, name='PhotodiodeBoard', authors='Allen Institute', repository_url='https://github.com/AllenNeuralDynamics/harp.device.PhotodiodeBoard', project_url='https://github.com/AllenNeuralDynamics/harp.device.PhotodiodeBoard'),
    WhoAmI.RfidReader: DeviceRecord(whoami=WhoAmI.RfidReader, name='RfidReader', authors='harp-tech', repository_url='https://github.com/harp-tech/device.rfidreader', project_url='https://github.com/harp-tech/device.rfidreader'),
    WhoAmI.Pluma: DeviceRecord(whoami=WhoAmI.Pluma, name='Pluma', authors='NeuroGEARS', repository_url='https://github.com/emotional-cities/pluma', project_url='https://github.com/emotional-cities/pluma'),
    WhoAmI.FastStepper: DeviceRecord(whoami=WhoAmI.FastStepper, name='FastStepper', authors='harp-tech', repository_url='https://github.com/harp-tech/device.faststepper', project_url='https://github.com/harp-tech/device.faststepper'),
})
"""The record of each registered device."""
