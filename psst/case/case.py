import os
import logging

import pandas as pd
import traitlets as t
import traittypes as tt
import ipywidgets as ipyw
from collections import OrderedDict

from . import matpower
from .generator import Generator
from .bus import Bus

logger = logging.getLogger(__name__)


class Case(t.HasTraits):

    name = t.Unicode()
    gen = tt.DataFrame()
    bus = tt.DataFrame()
    load = tt.DataFrame()
    branch = tt.DataFrame()
    bus_name = t.List(t.Unicode())
    gen_name = t.List(t.Unicode())
    branch_name = t.List(t.Unicode())
    unique_gen_names = t.Bool(default_value=True)
    _attributes = t.List(t.Unicode())

    def __init__(self, filename=None, *args, **kwargs):

        super(Case, self).__init__(*args, **kwargs)

        self.gen = pd.DataFrame(columns=list(Generator().traits().keys()))
        self.gen = self.gen.set_index('name')

        self.bus = pd.DataFrame(columns=list(Bus().traits().keys()))
        self.bus = self.bus.set_index('name')

        if filename is None:
            self.load_default_case()

        elif filename.endswith('.m'):
            self._attributes = list()
            self.read_matpower(filename)

        else:
            raise NotImplementedError(
                "Unsupported filetype .{fileextension} in {filename}. Please contact the developer".format(
                    fileextension=filename.split('.')[-1],
                    filename=filename
                )
            )

    def load_default_case(self):

        self.add_generator(name='GenCo0', maximum_real_power=100, generator_bus='Bus1')
        self.add_generator(name='GenCo1', maximum_real_power=200, generator_bus='Bus2')

    def add_generator(self, **kwargs):

        model = Generator(**kwargs)
        d = OrderedDict()
        for i in sorted(model.traits().keys()):
            d[i] = getattr(model, i)
        name = d.pop('name')
        self.gen.loc[name] = d

        return model

    def add_bus(self, **kwargs):

        model = Bus(**kwargs)
        d = OrderedDict()
        for i in sorted(model.traits().keys()):
            d[i] = getattr(model, i)
        name = d.pop('name')
        self.bus.loc[name] = d

        return model


    def read_matpower(self, filename, auto_assign_names=True, fill_loads=True, remove_empty=True, reset_generator_status=True):

        with open(os.path.abspath(filename)) as f:
            string = f.read()

        gen_list = list()
        for attribute in matpower.find_attributes(string):
            _list = matpower.parse_file(attribute, string)
            if attribute == 'gen':
                for row in _list:
                    model = Generator(**dict(zip(row, row)))
                    s = pd.Series(model._trait_values)
                    gen_list.append(s)

        self.gen = pd.DataFrame(gen_list)


class CaseView(ipyw.VBox):

    case = t.Instance(Case)

    def __init__(self, case, *args, **kwargs):

        self.case = case

        super(CaseView, self).__init__(**kwargs)

        self.generator_names = ipyw.Dropdown(
            options=list(self.case.gen.index)
        )

        children = [
            self.generator_names,
        ]

        self.children = children
