import season

class Controller(wiz.controller("user")):
    def __init__(self):
        super().__init__()

        wiz.model("security").require_admin("admin_controller_access")
