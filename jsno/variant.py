import dataclasses
import functools


@dataclasses.dataclass
class VariantTagging:
    family: "VariantFamily"
    tag_value: str

    @property
    def tag_name(self):
        return self.family.tag_name


@functools.singledispatch
def get_variant_tagging(arg):
    """
    Get the tagging info for a value. Used as a dispatch table, as
    singledispatch implements the mro resolution algorithm,
    """
    return None


class VariantFamilyBase:
    pass


def variant_family(tag_name: str) -> type:
    """
    Create a new variant family class
    """

    name = tag_name  # circumventing scoping problems

    class VariantFamily(VariantFamilyBase):
        class_by_tag = {}
        tag_name = name

        def __new__(cls, tag_value):

            def decorator(variant_cls):
                cls.class_by_tag[tag_value] = variant_cls

                tagging = VariantTagging(family=VariantFamily, tag_value=tag_value)

                @get_variant_tagging.register(variant_cls)
                def _(arg):
                    return tagging

                return variant_cls

            return decorator

        @classmethod
        def get_variant(cls, tag):
            return cls.class_by_tag.get(tag)

    return VariantFamily
