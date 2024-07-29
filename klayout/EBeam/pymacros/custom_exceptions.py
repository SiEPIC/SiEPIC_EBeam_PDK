class PCellRegistrationError(Exception):
    """
    Raised when a PCell is not properly registered in a library. This occurs when
    a PCell's .py file is in a library's folder but has not been registered in the library layout
    """

    def __init__(self, pcell, library):
        self.pcell = pcell
        self.library = library
        super().__init__(
            "Pcell {} could not be registered in library {}".format(pcell, library)
        )


class PCellInstantiationError(Exception):
    """
    Raised when a PCell is empty (not containing instances nor any shapes) when instantiated in a
    new layout
    """

    def __init__(self, pcell, library):
        self.pcell = pcell
        super().__init__(
            "Pcell {} from library {} is empty when instantiated in a new layout".format(
                pcell, library
            )
        )


class LibraryNotRegistered(Exception):
    """
    Raised when a library is not registered in Klayout
    """

    def __init__(self, library):
        self.library = library
        super().__init__("Library {} is not registered in KLayout".format(library))


class PCellImplementationError(Exception):
    """
    Raised when an error arises when trying to produce the pcell. These errors are displayed in the error layer
    in KLayout.
    """

    def __init__(self, pcell, library, error):
        self.library = library
        super().__init__(
            "Error {} for pcell {} in library {}".format(error, pcell, library)
        )
