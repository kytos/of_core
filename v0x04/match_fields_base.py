"""Base classes for Match Fields."""

from abc import ABC, abstractmethod


class MatchField(ABC):
    """Base class for match fields. Abstract OXM TLVs of python-openflow.

    Just extend this class and you will be forced to define the required
    low-level attributes and methods below:

    * "name" attribute (field name to be displayed in JSON);
    * "oxm_field" attribute (``OxmOfbMatchField`` enum);
    * Method to return a pyof OxmTLV;
    * Method to create an instance from an OxmTLV.
    """

    def __init__(self, value):
        """Define match field value."""
        self.value = value

    @property
    @classmethod
    @abstractmethod
    def name(cls):
        """Define a name to be displayed in JSON.

        It can be overriden just by a class attibute.
        """

    @property
    @classmethod
    @abstractmethod
    def oxm_field(cls):
        """Define this subclass ``OxmOfbMatchField`` value.

        It can be overriden just by as a class attibute.
        """

    @abstractmethod
    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""

    @classmethod
    @abstractmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""

    def __eq__(self, other):
        """Two objects are equal if their values are the same.

        The oxm_field equality is checked indirectly when comparing whether
        the objects are instances of the same class.
        """
        return isinstance(other, self.__class__) and other.value == self.value


class MatchFieldFactory(ABC):
    """Create the correct MatchField subclass instance.

    As OF 1.3 has many match fields and there are many ways to (un)pack their
    OxmTLV.oxm_value, this class does all the work of finding the correct
    MatchField class and instantiating the corresponding object.
    """

    __classes = {}

    @classmethod
    def from_name(cls, name, value):
        """Return the proper object from name and value."""
        field_class = cls._get_class(name)
        if field_class:
            return field_class(value)
        return None

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return the proper object from a pyof OXM TLV."""
        field_class = cls._get_class(tlv.oxm_field)
        if field_class:
            return field_class.from_of_tlv(tlv)
        return None

    @classmethod
    def _get_class(cls, name_or_field):
        """Return the proper object from field name or OxmTLV.oxm_field."""
        if not cls.__classes:
            cls._index_classes()
        return cls.__classes.get(name_or_field)

    @classmethod
    def _index_classes(cls):
        for subclass in MatchField.__subclasses__():
            cls.__classes[subclass.name] = subclass
            cls.__classes[subclass.oxm_field] = subclass
