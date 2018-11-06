from Database.database import Heartrate, Steps, User, Position, Sleep, CustomAttribute, Acceleration


class Device:
    """ The device class is initials standard variables and methods.
        It is the parent class of the individual method classes.
    """
    
    def __init__(self):
        self.heartrate = Heartrate()
        self.steps = Steps()
        self.user = User()
        self.position = Position()
        self.sleep = Sleep()
        self.acceleration = Acceleration()
        self.custom_attributes = CustomAttribute()

        self.support_hearate = False
        self.support_acceleration = False
        self.support_steps = False
        self.support_user = False
        self.support_sleep = False
        self.support_position = False
        self.support_custom_attributes= False

    def getHeartrate(self):
        return self.heartrate
        
    def getSteps(self):
        return self.steps
        
    def getUser(self):
        return self.user

    def getPosition(self):
        return self.position
    
    def getSleep(self):
        return self.sleep

    def getAcceleration(self):
        return self.acceleration

    def getCustomAttributes(self):
        return self.custom_attributes

    def action(self):
        raise NotImplementedError("Function action of your used method is not implemented yet")
