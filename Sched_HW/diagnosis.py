from cnf import *
from ortools.sat.python import cp_model

objects = ['Outlet', 'Rasp-Pi', 'Power-Board',
           'Arduino', 'Sensor-Board0', 'Sensor-Board1']
actuators = ['Fans', 'LEDs', 'Pump']
sensors = ['H-T0', 'Light0', 'Moisture0', 'H-T1', 'Light1', 'Moisture1',
           'Wlevel']
relations = ['working', 'connected', 'powered', 'signal', 'expected-result']

def powered(comp): return f'powered({comp})'
def working(comp): return f'working({comp})'
def connected(from_comp, to_comp):
    return f'connected({from_comp}, {to_comp})'
def signal(signal, component): return f'signal({signal}, {component})'
def rasp_pi_signal(the_signal): return signal(the_signal, 'Rasp-Pi')
def expected_result(actuator): return f'expected-result({actuator})'

def create_relation(name, model, variables):
    variables[name] = model.NewBoolVar(name)

def create_relations(relations, model, variables):
    for relation in relations: create_relation(relation, model, variables)

def create_working_relations(model, variables):
    create_relations([working(comp) for comp in objects + actuators + sensors],
                     model, variables)

def create_connected_relations(model, variables):
    # Examples are: connected(H-T0, Sensor-Board0)
    #               connected(Arduino, Rasp-Pi)
    # BEGIN STUDENT CODE
    connections = [
        # Power connections
        ('Outlet', 'Rasp-Pi'),
        ('Outlet', 'Power-Board'),
        ('Power-Board', 'Fans'),
        ('Power-Board', 'LEDs'),
        ('Power-Board', 'Pump'),

        # Sensor -> Sensor Board
        ('H-T0', 'Sensor-Board0'),
        ('Light0', 'Sensor-Board0'),
        ('Moisture0', 'Sensor-Board0'),

        ('H-T1', 'Sensor-Board1'),
        ('Light1', 'Sensor-Board1'),
        ('Moisture1', 'Sensor-Board1'),

        # Sensor Boards / Wlevel -> Arduino
        ('Sensor-Board0', 'Arduino'),
        ('Sensor-Board1', 'Arduino'),
        ('Wlevel', 'Arduino'),

        # Arduino <-> Rasp-Pi
        ('Arduino', 'Rasp-Pi'),
        ('Rasp-Pi', 'Arduino'),

        # Arduino -> Power Board
        ('Arduino', 'Power-Board')
    ]

    create_relations(
        [connected(a, b) for a, b in connections],
        model,
        variables
    )

    # END STUDENT CODE
    pass

def create_powered_relations(model, variables):
    # Examples are: powered(Outlet), powered(Fans)
    # BEGIN STUDENT CODE
    powered_components = [
        'Outlet',
        'Rasp-Pi',
        'Power-Board',
        'Fans',
        'LEDs',
        'Pump'
    ]

    create_relations(
        [powered(comp) for comp in powered_components],
        model,
        variables
    )
    # END STUDENT CODE
    pass

def create_signal_relations(model, variables):
    # Examples are: signal(H-T0, H-T0),
    #               signal(H-T0, Sensor-Board0)
    #               signal(Pump, Power-Board)
    # BEGIN STUDENT CODE
    signal_relations = []

    # 1. Each sensor generates its own signal
    for sensor_name in sensors:
        signal_relations.append(
            signal(sensor_name, sensor_name)
        )

    # 2. Sensor-Board0 receives its three sensor signals
    for sensor_name in ['H-T0', 'Light0', 'Moisture0']:
        signal_relations.append(
            signal(sensor_name, 'Sensor-Board0')
        )

    # 3. Sensor-Board1 receives its three sensor signals
    for sensor_name in ['H-T1', 'Light1', 'Moisture1']:
        signal_relations.append(
            signal(sensor_name, 'Sensor-Board1')
        )

    # 4. Arduino receives all seven sensor signals
    for sensor_name in sensors:
        signal_relations.append(
            signal(sensor_name, 'Arduino')
        )

    # 5. Rasp-Pi receives all seven sensor signals
    for sensor_name in sensors:
        signal_relations.append(
            signal(sensor_name, 'Rasp-Pi')
        )

    # 6. Rasp-Pi generates actuator signals
    for actuator in actuators:
        signal_relations.append(
            signal(actuator, 'Rasp-Pi')
        )

    # 7. Arduino receives actuator signals
    for actuator in actuators:
        signal_relations.append(
            signal(actuator, 'Arduino')
        )

    # 8. Power-Board receives actuator signals
    for actuator in actuators:
        signal_relations.append(
            signal(actuator, 'Power-Board')
        )

    create_relations(signal_relations, model, variables)
    # END STUDENT CODE
    pass

def create_expected_result_relations(model, variables):
    # Example is: expected-result(LEDs)
    # BEGIN STUDENT CODE
    create_relations(
        [expected_result(actuator) for actuator in actuators],
        model,
        variables
    )
    # END STUDENT CODE
    pass

def create_relation_variables(model):
    variables = {}
    create_working_relations(model, variables)
    create_connected_relations(model, variables)
    create_powered_relations(model, variables)
    create_signal_relations(model, variables)
    create_expected_result_relations(model, variables)
    return variables

def add_constraint_to_model(constraint, model, variables):
    for disj in (eval(constraint) if isinstance(constraint, str) else constraint):
        conv_disj = [variables[lit] if not is_negated(lit) else
                     variables[lit[1]].Not() for lit in disj]
        model.AddBoolOr(conv_disj)

def create_powered_constraint(from_comp, to_comp, model, variables):
    constraint = f"IFF('{powered(to_comp)}', AND('{connected(from_comp, to_comp)}',\
                                                 '{working(from_comp)}'))"
    add_constraint_to_model(constraint, model, variables)

def create_powered_actuator_constraint(actuator, model, variables):
    constraint = f"IFF('{powered(actuator)}',\
                       AND('{connected('Power-Board', actuator)}',\
                           AND('{powered('Power-Board')}',\
                               AND('{working('Power-Board')}', '{signal(actuator, 'Power-Board')}'))))"
    add_constraint_to_model(constraint, model, variables)

def create_powered_constraints(model, variables):
    add_constraint_to_model(LIT(powered('Outlet')), model, variables)
    create_powered_constraint('Outlet', 'Rasp-Pi', model, variables)
    create_powered_constraint('Outlet', 'Power-Board', model, variables)
    for actuator in actuators:
        create_powered_actuator_constraint(actuator, model, variables)

def create_signal_constraints(model, variables):
    # An example is: IFF('signal(H-T0, Sensor-Board0)',
    #                    AND('connected(H-T0, Sensor-Board0)', AND('working(H-T0)', 'signal(H-T0, H-T0)')))
    # BEGIN STUDENT CODE
    for sensor in ['H-T0', 'Light0', 'Moisture0']:
        constraint = f"IFF('{signal(sensor, 'Sensor-Board0')}',\
                    AND('{connected(sensor, 'Sensor-Board0')}',\
                        AND('{working(sensor)}', '{signal(sensor, sensor)}')))"
        add_constraint_to_model(constraint, model, variables)

    for sensor in ['H-T1', 'Light1', 'Moisture1']:
        constraint = f"IFF('{signal(sensor, 'Sensor-Board1')}',\
                      AND('{connected(sensor, 'Sensor-Board1')}',\
                          AND('{working(sensor)}', '{signal(sensor, sensor)}')))"
        add_constraint_to_model(constraint, model, variables)

    for sensor in ['H-T0', 'Light0', 'Moisture0']:
        constraint = f"IFF('{signal(sensor, 'Arduino')}',\
                      AND('{connected('Sensor-Board0', 'Arduino')}',\
                          AND('{working('Sensor-Board0')}', '{signal(sensor, 'Sensor-Board0')}')))"
        add_constraint_to_model(constraint, model, variables)

    for sensor in ['H-T1', 'Light1', 'Moisture1']:
        constraint = f"IFF('{signal(sensor, 'Arduino')}',\
                      AND('{connected('Sensor-Board1', 'Arduino')}',\
                          AND('{working('Sensor-Board1')}', '{signal(sensor, 'Sensor-Board1')}')))"
        add_constraint_to_model(constraint, model, variables)

    constraint = f"IFF('{signal('Wlevel', 'Arduino')}',\
                  AND('{connected('Wlevel', 'Arduino')}',\
                      AND('{working('Wlevel')}', '{signal('Wlevel', 'Wlevel')}')))"
    add_constraint_to_model(constraint, model, variables)

    for sensor in sensors:
        constraint = f"IFF('{signal(sensor, 'Rasp-Pi')}',\
                      AND('{connected('Arduino', 'Rasp-Pi')}',\
                          AND('{working('Arduino')}', '{signal(sensor, 'Arduino')}')))"
        add_constraint_to_model(constraint, model, variables)

    for actuator in actuators:
        constraint = f"IFF('{signal(actuator, 'Arduino')}',\
                      AND('{connected('Rasp-Pi', 'Arduino')}',\
                          AND('{working('Rasp-Pi')}', '{signal(actuator, 'Rasp-Pi')}')))"
        add_constraint_to_model(constraint, model, variables)

    for actuator in actuators:
        constraint = f"IFF('{signal(actuator, 'Power-Board')}',\
                      AND('{connected('Arduino', 'Power-Board')}',\
                          AND('{working('Arduino')}', '{signal(actuator, 'Arduino')}')))"
        add_constraint_to_model(constraint, model, variables)
    # END STUDENT CODE
    pass

def create_sensor_generation_constraints(model, variables):
    # An example is: IFF('working(H-T0)', 'signal(H-T0, H-T0)')
    # BEGIN STUDENT CODE
    for sensor in sensors:
        constraint = f"IFF('{working(sensor)}',\
                      '{signal(sensor, sensor)}')"
        add_constraint_to_model(constraint, model, variables)
    # END STUDENT CODE
    pass

def create_expected_result_constraints(model, variables):
    # Examples are: IFF('expected-result(Fans)',
    #                   AND('powered(Fans)', AND('working(Fans)', OR('signal(H-T0, Rasp-Pi)', 'signal(H-T1, Rasp-Pi)'))))
    #               IFF('expected-result(Pump)',
    #                    AND('powered(Pump)', AND('working(Pump)', OR(OR('signal(Moisture0, Rasp-Pi)', 'signal(Moisture1, Rasp-Pi)'),
    #                                                                'signal(Wlevel, Rasp-Pi)'))))
    # BEGIN STUDENT CODE
    constraint = f"IFF('{expected_result('Fans')}',\
                  AND('{powered('Fans')}',\
                      AND('{working('Fans')}',\
                          OR('{signal('H-T0', 'Rasp-Pi')}', '{signal('H-T1', 'Rasp-Pi')}'))))"
    add_constraint_to_model(constraint, model, variables)

    constraint = f"IFF('{expected_result('LEDs')}',\
                  AND('{powered('LEDs')}',\
                      AND('{working('LEDs')}',\
                          OR('{signal('Light0', 'Rasp-Pi')}', '{signal('Light1', 'Rasp-Pi')}'))))"
    add_constraint_to_model(constraint, model, variables)

    constraint = f"IFF('{expected_result('Pump')}',\
                  AND('{powered('Pump')}',\
                      AND('{working('Pump')}',\
                          OR(OR('{signal('Moisture0', 'Rasp-Pi')}', '{signal('Moisture1', 'Rasp-Pi')}'),\
                             '{signal('Wlevel', 'Rasp-Pi')}'))))"
    add_constraint_to_model(constraint, model, variables)

    # END STUDENT CODE
    pass

def create_constraints(model, variables):
    create_powered_constraints(model, variables)
    create_signal_constraints(model, variables)
    create_sensor_generation_constraints(model, variables)
    create_expected_result_constraints(model, variables)

def create_greenhouse_model():
    model = cp_model.CpModel()
    variables = create_relation_variables(model)
    create_constraints(model, variables)
    return (model, variables)
    
def collect_diagnosis(solver, variables):
    return set([var for var in variables
                if ((var.startswith('connected') or var.startswith('working')) and
                    solver.BooleanValue(variables[var]) == False)])

class DiagnosesCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, variables):
        cp_model.CpSolverSolutionCallback.__init__(self)
        # BEGIN STUDENT CODE
        self.variables = variables
        self.diagnoses = []
        # END STUDENT CODE

    def OnSolutionCallback(self):
        # Extract the connected and working relations that are False
        # BEGIN STUDENT CODE
        diagnosis = collect_diagnosis(self, self.variables)
        if diagnosis not in self.diagnoses:
            self.diagnoses.append(diagnosis)
        # END STUDENT CODE
        pass

def diagnose(observations):
    model, variables = create_greenhouse_model()
    add_constraint_to_model(observations, model, variables)

    collector = DiagnosesCollector(variables)
    diagnoses = []
    solver = cp_model.CpSolver()
    solver.SearchForAllSolutions(model, collector)
    # Remove all redundant diagnoses (those that are supersets
    #   of other diagnoses).
    # BEGIN STUDENT CODE
    for diagnosis in collector.diagnoses:
        redundant = False
        for other in collector.diagnoses:
            if other < diagnosis:
                redundant = True
                break
        if not redundant:
            diagnoses.append(diagnosis)
            
    diagnoses.sort(key=len)
    # END STUDENT CODE

    return diagnoses
