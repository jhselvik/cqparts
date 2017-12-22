
from ..params import *

from .base import Fastener, FastenerMalePart
from .params import HeadType, DriveType, ThreadType
from .utils import VectorEvaluator, Selector, Applicator
from ..solidtypes import threads
from ..constraint import Mate, Coincident
from ..utils import CoordSystem

import logging
log = logging.getLogger(__name__)


class Screw(FastenerMalePart):
    """
    Part representing a single screw
    """

    head = HeadType(
        default=('countersunk', {
            'diameter': 9.5,
            'height': 3.5,
        }),
        doc="head type and parameters"
    )
    drive = DriveType(
        default=('phillips', {
            'diameter': 5.5,
            'depth': 2.5,
            'width': 1.15,
        }),
        doc="screw drive type and parameters"
    )
    thread = ThreadType(
        default=('triangular', {
            'diameter': 5,
            'pitch': 2,
            'angle': 20,
        }),
        doc="thread type and parameters",
    )
    neck_taper = FloatRange(0, 90, 15, doc="angle of neck's taper (0 is parallel with neck)")
    neck_length = PositiveFloat(7.5, doc="length of neck")
    length = PositiveFloat(25, doc="screw's length")
    tip_length = PositiveFloat(5, doc="length of taper on a pointed tip")


class ScrewFastener(Fastener):
    Evaluator = VectorEvaluator

    class Selector(Selector):
        def get_components(self):
            log.info("ScrewFastener.Selector.get_components()")
            return {'screw': Screw(
                head=('countersunk', {
                    'diameter': 9.5,
                    'height': 3.5,
                }),
                neck_length=abs(self.evaluation.eval[-1].start_point - self.evaluation.location.origin),
                # only the length after the neck is threaded
                length=abs(self.evaluation.eval[-1].end_point - self.evaluation.location.origin),
            )}

        def get_constraints(self):
            # bind fastener relative to its anchor; the part holding it in.
            anchor_part = self.evaluation.eval[-1].part  # last effected part
            return [Coincident(
                self.components['screw'].mate_origin,
                Mate(anchor_part, self.evaluation.location - anchor_part.world_coords)
            )]

    class Applicator(Applicator):
        def apply(self):
            screw = self.selector.components['screw']
            cutter = screw.make_cutter()  # cutter in local coords

            for effect in self.evaluation.eval:
                log.warning("cutting into: %r", effect.part)
                relative_coordsys = screw.world_coords - effect.part.world_coords
                local_cutter = relative_coordsys + cutter
                effect.part.local_obj = effect.part.local_obj.cut(local_cutter)
