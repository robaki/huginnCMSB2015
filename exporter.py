#! /usr/bin/env python3
# I, Robert Rozanski, the copyright holder of this work, release this work into the public domain. This applies worldwide. In some countries this may not be legally possible; if so: I grant anyone the right to use this work for any purpose, without any conditions, unless such conditions are required by law.

import mnm_repr
import exp_repr

from exp_repr import DetectionEntity, LocalisationEntity, DetectionActivity, AdamTwoFactorExperiment
from mnm_repr import Activity, Condition

def export_entities(entities):
	strings = []
	for ent in entities:
		if isinstance(ent, mnm_repr.Gene):
			strings.append("\ngene(%s,%s)." %(ent.ID, ent.version))
		elif isinstance(ent, mnm_repr.Metabolite):
			strings.append("\nmetabolite(%s,%s)." %(ent.ID, ent.version))
		elif isinstance(ent, mnm_repr.Protein):
			strings.append("\nprotein(%s,%s)." %(ent.ID, ent.version))
		elif isinstance(ent, mnm_repr.Complex):
			strings.append("\ncomplex(%s,%s)." %(ent.ID, ent.version))
		else:
			raise TypeError("export_entities: entity type not recognised:%s" % type(ent))

		if ent.properties == frozenset([]):
			continue

		for prop in ent.properties:
			if isinstance(prop, mnm_repr.Catalyses):
				strings.append("\ncatalyses(%s,%s,%s)." % (ent.ID, ent.version, prop.activity.ID))
			elif isinstance(prop, mnm_repr.Transports):
				strings.append("\ntransports(%s,%s,%s)." % (ent.ID, ent.version, prop.activity.ID))
			else:	
				raise TypeError("export_entities: property type not recognised:%s" % type(prop))

	return strings


def export_compartments(compartments):
	comps = ";".join([comp.ID for comp in compartments])
	return [comps.join(['\ncompartment(', ').'])]


def export_activities(activities):
	strings = []
	for act in activities:
		if isinstance(act, mnm_repr.Growth):
			strings.append('\ngrowth(%s).' % act.ID)
		elif isinstance(act, mnm_repr.Expression):
			strings.append('\nexpression(%s).' % act.ID)
		elif isinstance(act, mnm_repr.Reaction):
			strings.append('\nreaction(%s).' % act.ID)
		elif isinstance(act, mnm_repr.Transport):
			strings.append('\ntransport(%s).' % act.ID)
		elif isinstance(act, mnm_repr.ComplexFormation):
			strings.append('\ncomplex_formation(%s).' % act.ID)
		else:
			raise TypeError("export_activities: activity type not recognised: %s" % type(act))

	for act in activities:
		strings.extend(export_activity(act))
	return strings


def export_activity(activity):
	strings = []
	for req in activity.required_conditions:
		if isinstance(req, mnm_repr.PresentEntity):
			strings.append('\nsubstrate(%s,%s,%s,%s).' % (req.entity.ID, req.entity.version, req.compartment.ID, activity.ID))
		elif isinstance(req, mnm_repr.PresentCatalyst):		
			strings.append('\nenz_required(%s).' % activity.ID)
			strings.append('\nenz_compartment(%s,%s).' % (req.compartment.ID, activity.ID))
		elif isinstance(req, mnm_repr.PresentTransporter):
			strings.append('\ntransp_required(%s).' % activity.ID)
			strings.append('\ntransp_compartment(%s,%s).' % (req.compartment.ID, activity.ID))
		else:
			raise TypeError("export_activity: requirement type not recognised:%s" % type(req))

	for change in activity.changes:
		strings.append('\nproduct(%s,%s,%s,%s).' % (change.entity.ID, change.entity.version, change.compartment.ID, activity.ID))

	return strings


def export_results(results):
	strings = []
	for result in results:
		ID = result.ID
		out = result.outcome
		if isinstance(result.exp_description.experiment_type, exp_repr.ReconstructionTransporterRequired):
			act = result.exp_description.experiment_type.transport_activity_id
			trp = result.exp_description.experiment_type.transporter_id
			strings.append('\nresult(%s, experiment(transp_reconstruction_exp, %s, %s), %s).' % (ID, act, trp, out))

		elif isinstance(result.exp_description.experiment_type, exp_repr.ReconstructionEnzReaction):
			act = result.exp_description.experiment_type.reaction_id
			enz = result.exp_description.experiment_type.enzyme_id
			strings.append('\nresult(%s, experiment(enz_reconstruction_exp, %s, %s), %s).' % (ID, act, enz, out))

		elif isinstance(result.exp_description.experiment_type, exp_repr.ReconstructionActivity):
			act = result.exp_description.experiment_type.activity_id
			strings.append('\nresult(%s, experiment(basic_reconstruction_exp, %s), %s).' % (ID, act, out))

		elif isinstance(result.exp_description.experiment_type, exp_repr.AdamTwoFactorExperiment):
			gene = result.exp_description.experiment_type.gene_id
			met = result.exp_description.experiment_type.metabolite_id
			strings.append('\nresult(%s, experiment(adam_two_factor_exp, %s, %s), %s).' % (ID, gene, met, out))

		elif isinstance(result.exp_description.experiment_type, exp_repr.DetectionActivity):
			act = result.exp_description.experiment_type.activity_id
			strings.append('\nresult(%s, experiment(detection_activity_exp, %s), %s).' % (ID, act, out))

		elif isinstance(result.exp_description.experiment_type, exp_repr.LocalisationEntity):
			ent = result.exp_description.experiment_type.entity_id
			comp = result.exp_description.experiment_type.compartment_id
			strings.append('\nresult(%s, experiment(localisation_entity_exp, %s, %s), %s).' % (ID, ent, comp, out))

		elif isinstance(result.exp_description.experiment_type, exp_repr.DetectionEntity):
			ent = result.exp_description.experiment_type.entity_id
			strings.append('\nresult(%s, experiment(detection_entity_exp, %s), %s).' % (ID, ent, out))

		else:
			raise TypeError('export_results: result type not recognised:%s' % type(result))

	return strings


def export_models(models_results):
	strings = []
	# model().
	joined_models = ';'.join([x.ID for x in models_results.keys()])
	strings.append(joined_models.join(['\nmodel(', ').']))
	# specification:
	for model in models_results.keys():
		strings.extend(export_model_specification(model))

	return strings
	
def export_model_specification(model):
	strings = []
	# setup
	for cond in model.setup_conditions:
		strings.append('\nadded_to_model(setup_present(%s,%s,%s),%s).' % (cond.entity.ID, cond.entity.version, cond.compartment.ID, model.ID))
	# activities
	for act in model.intermediate_activities:
		strings.append('\nadded_to_model(%s,%s).' % (act.ID, model.ID))

	return strings


def export_termination_conds_revision(base_model):
	strings = []
	for cond in base_model.termination_conditions:
		strings.append('\n#example synthesizable(%s, %s, %s, %s).' % (cond.entity.ID, cond.entity.version, cond.compartment.ID, base_model.ID))
	# base model shouldn't have inactive activities or more than one version of any entity (would restrict derived models too, so OK)
	strings.append('\n#example not not_clean_model(%s).' % base_model.ID)
	return strings


def export_relevancy_results_revision(models_results):
	strings = []
	for model in models_results.keys():
		for res in models_results[model]:
			strings.append('\nrelevant(%s, %s).' % (res.ID, model.ID))
			strings.append('\n#example not inconsistent(%s, %s).' % (model.ID, res.ID))
	return strings


def export_termination_conds_consistency(base_model):
	strings = []
	for cond in base_model.termination_conditions:
		strings.append('\n:- not synthesizable(%s, %s, %s, %s).' % (cond.entity.ID, cond.entity.version, cond.compartment.ID, base_model.ID))
	# base model shouldn't have inactive activities or more than one version of any entity (would restrict derived models too, so OK)
	strings.append('\n:- not_clean_model(%s).' % base_model.ID)
	return strings


def export_relevancy_results_consistency(models_results, base_model):
	strings = []
	for model in models_results.keys():
		for res in models_results[model]:
			if res in base_model.ignored_results:
				continue
			else:
				strings.append('\nrelevant(%s, %s).' % (res.ID, model.ID))
				strings.append('\n:- inconsistent(%s, %s).' % (model.ID, res.ID))
	return strings


def export_force_new_model(base_model, external_models):
	strings = []
	for model in external_models:
		# external model specification
		strings.append('\nexternal_model(%s).' % model.ID)
		for activity in model.intermediate_activities:
			strings.append('\nin_model(%s,%s).' % (activity.ID, model.ID))
		# constraint
		strings.append('\n#example different(%s, %s).' % (base_model.ID, model.ID))
	return strings


def export_add_activities(activities):
	return ['\n#modeh add(%s) =%s @1.' % (act.ID, act.add_cost) for act in activities]


def export_remove_activities(activities):
	return ['\n#modeh remove(%s) =%s @1.' % (act.ID, act.remove_cost) for act in activities]


def export_ignore_results(results):
	return ['\n#modeh ignored(%s) =%s @2.' % (result.ID, result.exp_description.experiment_type.ignoring_penalty) for result in results]


def models_rules(max_number_activities):
	return ['\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\n%%%%% model specification rules %%%%%',
	'\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\nactivity(Activity) :- reaction(Activity).',
	'\nactivity(Activity) :- transport(Activity).',
	'\nactivity(Activity) :- expression(Activity).',
	'\nactivity(Activity) :- complex_formation(Activity).',
	'\nactivity(Activity) :- growth(Activity).',
	'\n',
	'\nentity(Entity, Version) :- metabolite(Entity, Version).',
	'\nentity(Entity, Version) :- complex(Entity, Version).',
	'\nentity(Entity, Version) :- protein(Entity, Version).',
	'\nentity(Entity, Version) :- gene(Entity, Version).',
	'\n',
	'\nconnected_compartments(Compartment2,Compartment1) :- connected_compartments(Compartment1,Compartment2).',
	'\nconnected_compartments(Compartment,Compartment) :- compartment(Compartment).',
	'\n',
	'\nin_model(ActivityOrSetup, Model) :-',
	'\n	added_to_model(ActivityOrSetup, Model),',
	'\n	not removed(ActivityOrSetup, Model).',
	'\n',
	'\ninitially_present(Entity, Version, Compartment, Model) :-',
	'\n	in_model(setup_present(Entity, Version, Compartment), Model).',
	'\n',
	'\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\n%%%%% synthesizable Entity rules %%%%%',
	'\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\nsynthesizable(Ent, Version, Compartment, Model) :-',
	'\n	activity(Activity),',
	'\n	product(Ent, Version, Compartment, Activity),',
	'\n	active(Activity, Model).',
	'\n',
	'\nactive(Activity, Model) :-',
	'\n	activity(Activity),',
	'\n	in_model(Activity, Model),',
	'\n	not eliminated(Activity, Model).',
	'\n',
	'\neliminated(Activity, Model) :-',
	'\n	eliminated(Activity, Model, Int),',
	'\n	iteration(Int).',
	'\n',
	'\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\n%%%%% activities elimination rules %%%%%',
	'\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\n',
	'\n% iterations counter',
	'\niteration(0).',
	'\niteration(1).',
	'\n',
	'\niteration(Int+2) :-',
	'\n	Int < %s,' % max_number_activities,
	'\n	iteration(Int),',
	'\n	eliminated(Activity, Model, Int+1),',
	'\n	not eliminated(Activity, Model, Int),',
	'\n	in_model(Activity, Model),',
	'\n	activity(Activity),',
	'\n	model(Model).',
	'\n',
	'\n% reachability of one specie from another going only from products to substrates (i.e. back).',
	'\npath_back_from_to(EntFrom, VerFrom, CompFrom, EntTo, VerTo, CompTo, Model, 0) :-',
	'\n	product(EntFrom, VerFrom, CompFrom, Activity),',
	'\n	substrate(EntTo, VerTo, CompTo, Activity),',
	'\n	in_model(Activity, Model),',
	'\n	activity(Activity).',
	'\n',
	'\npath_back_from_to(EntFrom, VerFrom, CompFrom, EntTo, VerTo, CompTo, Model, 0) :-',
	'\n	product(EntFrom, VerFrom, CompFrom, Activity),',
	'\n	substrate(InterEnt, InterVer, InterComp, Activity),',
	'\n	in_model(Activity, Model),',
	'\n	path_back_from_to(InterEnt, InterVer, InterComp, EntTo, VerTo, CompTo, Model, 0).',
	'\n',
	'\n% reachability for subsequent iterations.',
	'\npath_back_from_to(EntFrom, VerFrom, CompFrom, EntTo, VerTo, CompTo, Model, Int+1) :-',
	'\n	iteration(Int),',
	'\n	product(EntFrom, VerFrom, CompFrom, Activity),',
	'\n	substrate(EntTo, VerTo, CompTo, Activity),',
	'\n	in_model(Activity, Model),',
	'\n	not eliminated(Activity, Model, Int), % not eliminated on previous iteration',
	'\n	activity(Activity).',
	'\n',
	'\npath_back_from_to(EntFrom, VerFrom, CompFrom, EntTo, VerTo, CompTo, Model, Int+1) :-',
	'\n	iteration(Int),',
	'\n	product(EntFrom, VerFrom, CompFrom, Activity),',
	'\n	substrate(InterEnt, InterVer, InterComp, Activity),',
	'\n	in_model(Activity, Model),',
	'\n	not eliminated(Activity, Model, Int), % not eliminated on previous iteration',
	'\n	path_back_from_to(InterEnt, InterVer, InterComp, EntTo, VerTo, CompTo, Model, Int+1).',
	'\n',
	'\n% is initially_present entity reachable from particular entity',
	'\npath_back_to_initially_present(EntFrom, VerFrom, CompFrom, Model, Int) :-',
	'\n	iteration(Int),',
	'\n	path_back_from_to(EntFrom, VerFrom, CompFrom, EntTo, VerTo, CompTo, Model, Int),',
	'\n	initially_present(EntTo, VerTo, CompTo, Model).',
	'\n',
	'\npath_back_to_initially_present(Ent, Ver, Comp, Model, Int) :-',
	'\n	iteration(Int),',
	'\n	initially_present(Ent, Ver, Comp, Model).',
	'\n',
	'\n% has enzymes/transporter',
	'\nhas_enzyme(Activity, Model, Int) :-',
	'\n	iteration(Int),',
	'\n	in_model(Activity, Model),',
	'\n	enz_required(Activity),',
	'\n	compartment(Comp),',
	'\n	enz_compartment(Comp, Activity),',
	'\n	catalyses(Entity, Version, Activity),',
	'\n	connected_compartments(SomeComp, Comp),',
	'\n	path_back_to_initially_present(Entity, Version, SomeComp, Model, Int).',
	'\n',
	'\nhas_transporter(Activity, Model, Int) :-',
	'\n	iteration(Int),',
	'\n	in_model(Activity, Model),',
	'\n	transp_required(Activity),',
	'\n	compartment(Comp),',
	'\n	transp_compartment(Comp, Activity),',
	'\n	transports(Entity, Version, Activity),',
	'\n	path_back_to_initially_present(Entity, Version, Comp, Model, Int).',
	'\n',
	'\n% elimination of activities',
	'\neliminated(Activity, Model, Int) :-',
	'\n	iteration(Int),',
	'\n	activity(Activity),',
	'\n	in_model(Activity, Model),',
	'\n	substrate(EntFrom, VerFrom, CompFrom, Activity),',
	'\n	not path_back_to_initially_present(EntFrom, VerFrom, CompFrom, Model, Int).',
	'\n',
	'\neliminated(Activity, Model, Int) :-',
	'\n	iteration(Int),',
	'\n	activity(Activity),',
	'\n	in_model(Activity, Model),',
	'\n	enz_required(Activity),',
	'\n	not has_enzyme(Activity, Model, Int).',
	'\n',
	'\neliminated(Activity, Model, Int) :-',
	'\n	iteration(Int),',
	'\n	activity(Activity),',
	'\n	in_model(Activity, Model),',
	'\n	transp_required(Activity),',
	'\n	not has_transporter(Activity, Model, Int).']


def predictions_rules():
	return ['\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\n%%%%% prediction rules %%%%%',
	'\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\n',
	'\ngrowth(dummy).',
	'\n',
	'\nindifferent(Model, Experiment) :-',
	'\n	not predicts(Model, Experiment, true),',
	'\n	not predicts(Model, Experiment, false),',
	'\n	model(Model),',
	'\n	designed(Experiment).',
	'\n',
	'\n% Adams reconstruction',
	'\n predicts(Model, experiment(adam_two_factor_exp, Gene, Metabolite), false) :-',
	'\n	not predicts(Model, experiment(detection_activity_exp, GrowthActivity), false),',
	'\n	growth(GrowthActivity),',
	'\n	not predicts(Model, experiment(adam_two_factor_exp, Gene, Metabolite), true),',
	'\n	involved(Gene, GeneVer, Model),',
	'\n	gene(Gene, GeneVer),',
	'\n	involved(Metabolite, MetVersion, Model),',
	'\n	metabolite(Metabolite, MetVersion).',
	'\n',
	'\n predicts(Model, experiment(adam_two_factor_exp, Gene, Metabolite), true) :-% for genes that produce enzymes',
	'\n	not predicts(Model, experiment(detection_activity_exp, GrowthActivity), false),',
	'\n	growth(GrowthActivity),',
	'\n	substrate(Gene, GeneVer, GeneComp, ExpressionAct),',
	'\n	compartment(GeneComp),',
	'\n	expression(ExpressionAct),',
	'\n	in_model(ExpressionAct, Model),',
	'\n	metabolite(Metabolite, MetVersion),',
	'\n	% expression produces a catalyst',
	'\n	product(Ent, Ver, Comp, ExpressionAct),',
	'\n	catalyses(Ent, Ver, Reaction),',
	'\n	in_model(Reaction, Model),',
	'\n	enz_required(Reaction),% redundancy, but better make sure (might also help the ASP solver)',
	'\n	enz_compartment(SomeComp, Reaction),',
	'\n	connected_compartments(Comp, SomeComp),',
	'\n	% metabolite is within accepted distance from the catalysed reaction',
	'\n	distance(Reaction, Metabolite, MetVersion, MetComp, Integer, Model),',
	'\n	compartment(MetComp).',
	'\n',
	'\n predicts(Model, experiment(adam_two_factor_exp, Gene, Metabolite), true) :-% for genes that produce subunits of enzymes',
	'\n	not predicts(Model, experiment(detection_activity_exp, GrowthActivity), false),',
	'\n	growth(GrowthActivity),',
	'\n	substrate(Gene, GeneVer, GeneComp, ExpressionAct),',
	'\n	compartment(GeneComp),',
	'\n	expression(ExpressionAct),',
	'\n	in_model(ExpressionAct, Model),',
	'\n	metabolite(Metabolite, MetVersion),',
	'\n	% expression produces sth that is involved in production of enzyme down the line',
	'\n	product(EntTo, VerTo, CompTo, ExpressionAct),',
	'\n	entity(EntFrom, VerFrom),',
	'\n	compartment(CompFrom),',
	'\n	path_back_from_to(EntFrom, VerFrom, CompFrom, EntTo, VerTo, CompTo, Model, Int),',
	'\n	int(Integer),',
	'\n	catalyses(EntFrom, VerFrom, Reaction),',
	'\n	% enzyme is in appropriate compartment',
	'\n	enz_compartment(SomeComp, Reaction),',
	'\n	connected_compartments(SomeComp, CompFrom),',
	'\n	compartment(SomeComp),',
	'\n	% metabolite is within accepted distance from the catalysed reaction',
	'\n	distance(Reaction, Metabolite, MetVersion, MetComp, Integer, Model),',
	'\n	compartment(MetComp).',
	'\n',
	'\nint(0;1;2).% distance goes up to 2',
	'\n',
	'\ndistance(ActivityFrom, EntTo, VerTo, CompTo, 0, Model) :-',
	'\n	product(EntTo, VerTo, CompTo, ActivityFrom),',
	'\n	in_model(ActivityFrom, Model),',
	'\n	reaction(ActivityFrom),% only metabolic reactions',
	'\n	enz_required(ActivityFrom).% optimisation - only these activities make sense in the context of experiment',
	'\n',
	'\ndistance(ActivityFrom, EntTo, VerTo, CompTo, Int+1, Model) :-',
	'\n	distance(ActivityFrom, InterEnt, InterVer, InterComp, Int, Model),',
	'\n	substrate(InterEnt, InterVer, InterComp, InterActivity),',
	'\n	product(EntTo, VerTo, CompTo, InterActivity),',
	'\n	in_model(InterActivity, Model),',
	'\n	reaction(InterActivity),% only metabolic reactions',
	'\n	Int < 2,',
	'\n	int(Int).',
	'\n',
	'\n',
	'\n% in vitro reconstruction: transporter required',
	'\npredicts(Model, experiment(transp_reconstruction_exp, Activity, Entity), true) :-',
	'\n	in_model(Activity, Model),',
	'\n	transp_required(Activity),',
	'\n	involved(Entity, Version, Model),',
	'\n	transports(Entity, Version, Activity).',
	'\n',
	'\npredicts(Model, experiment(transp_reconstruction_exp, Activity, Entity), false) :-',
	'\n	in_model(Activity, Model),',
	'\n	transp_required(Activity),',
	'\n	involved(Entity, Version, Model),% there is a version of the entity in the model',
	'\n	not transports(Entity, Version, Activity),% that doesnt transport that stuff',
	'\n	transports(Entity, OtherVersion, Activity).% but some propose that this entity could do that',
	'\n',
	'\n',
	'\n% in vitro reconstruction: enzymatic',
	'\npredicts(Model, experiment(enz_reconstruction_exp, Activity, Entity), true) :-',
	'\n	in_model(Activity, Model),',
	'\n	enz_required(Activity),',
	'\n	involved(Entity, Version, Model),',
	'\n	catalyses(Entity, Version, Activity).',
	'\n',
	'\npredicts(Model, experiment(enz_reconstruction_exp, Activity, Entity), false) :-',
	'\n	in_model(Activity, Model),',
	'\n	enz_required(Activity),',
	'\n	involved(Entity, Version, Model),% there is a version of the entity in the model',
	'\n	not catalyses(Entity, Version, Activity),% that doesnt catalyse the reaction',
	'\n	catalyses(Entity, OtherVersion, Activity).% but some propose that this entity could do that',
	'\n',
	'\n',
	'\n% in vitro reconstruction: basic',
	'\npredicts(Model, experiment(basic_reconstruction_exp, Activity), true) :-',
	'\n	activity(Activity),',
	'\n	in_model(Activity, Model),',
	'\n	not enz_required(Activity),',
	'\n	not transp_required(Activity).',
	'\n',
	'\n',
	'\n% localisation experiments: detecting entities',
	'\npredicts(Model, experiment(localisation_entity_exp, Entity, Compartment), true) :-',
	'\n	not predicts(Model, experiment(detection_activity_exp, GrowthActivity), false),',
	'\n	growth(GrowthActivity),',
	'\n	compartment(Compartment),',
	'\n	involved(Entity, Version, Model),',
	'\n	synthesizable(Entity, Version, Compartment, Model).',
	'\n',
	'\npredicts(Model, experiment(localisation_entity_exp, Entity, Compartment), true) :-',
	'\n	compartment(Compartment),',
	'\n	in_model(setup_present(Entity, Version, Compartment), Model).',
	'\n',
	'\npredicts(Model, experiment(localisation_entity_exp, Entity, Compartment), false) :-',
	'\n	not predicts(Model, experiment(detection_activity_exp, GrowthActivity), false),',
	'\n	growth(GrowthActivity),',
	'\n	compartment(Compartment),',
	'\n	involved(Entity, Version, Model),',
	'\n	not predicts(Model, experiment(localisation_entity_exp, Entity, Compartment), true).',
	'\n',
	'\n',
	'\n% detection experiments: detecting entities',
	'\npredicts(Model, experiment(detection_entity_exp, Entity), true) :-',
	'\n	not predicts(Model, experiment(detection_activity_exp, GrowthActivity), false),',
	'\n	growth(GrowthActivity),',
	'\n	compartment(Compartment),',
	'\n	involved(Entity, Version, Model),',
	'\n	synthesizable(Entity, Version, Compartment, Model).',
	'\n',
	'\npredicts(Model, experiment(detection_entity_exp, Entity), true) :-% for stuff in the setup',
	'\n	compartment(Compartment),',
	'\n	in_model(setup_present(Entity, Version, Compartment), Model).',
	'\n',
	'\npredicts(Model, experiment(detection_entity_exp, Entity), false) :-',
	'\n	not predicts(Model, experiment(detection_activity_exp, GrowthActivity), false),',
	'\n	growth(GrowthActivity),',
	'\n	involved(Entity, Version, Model),',
	'\n	not predicts(Model, experiment(detection_entity_exp, Entity), true).',
	'\n',
	'\n',
	'\n% growth experiments (or any other detecting activities)',
	'\npredicts(Model, experiment(detection_activity_exp, Activity), true) :-',
	'\n	not predicts(Model, experiment(detection_activity_exp, GrowthActivity), false),',
	'\n	growth(GrowthActivity),',
	'\n	in_model(Activity, Model),',
	'\n	activity(Activity),',
	'\n	active(Activity, Model).',
	'\n',
	'\npredicts(Model, experiment(detection_activity_exp, Activity), false) :-',
	'\n	not predicts(Model, experiment(detection_activity_exp, GrowthActivity), false),',
	'\n	growth(GrowthActivity),',
	'\n	in_model(Activity, Model),',
	'\n	activity(Activity),',
	'\n	not active(Activity, Model).',
	'\n',
	'\npredicts(Model, experiment(detection_activity_exp, GrowthActivity), false) :-',
	'\n	growth(GrowthActivity),',
	'\n	in_model(GrowthActivity, Model),',
	'\n	activity(GrowthActivity),',
	'\n	not active(GrowthActivity, Model).',
	'\n',
	'\n% involved species (to handle open world)',
	'\ninvolved(Entity, Version, Model) :-',
	'\n	compartment(Compartment),',
	'\n	initially_present(Entity, Version, Compartment, Model).',
	'\n',
	'\ninvolved(Entity, Version, Model) :-',
	'\n	compartment(Compartment),',
	'\n	product(Entity, Version, Compartment, Activity),',
	'\n	in_model(Activity, Model).',
	'\n',
	'\ninvolved(Entity, Version, Model) :-',
	'\n	compartment(Compartment),',
	'\n	substrate(Entity, Version, Compartment, Activity),',
	'\n	in_model(Activity, Model).']


def interventions_rules():
	return ['\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\n%%%%%% application of interventions to all models %%%%%%',
	'\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\n',
	'\nremoved(ActivityOrCondition, Model) :-',
	'\n	remove(ActivityOrCondition),',
	'\n	model(Model).',
	'\n',
	'\nadded_to_model(ActivityOrCondition, Model) :-',
	'\n	add(ActivityOrCondition),',
	'\n	model(Model).']


def inconsistency_rules():
	return ['\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\n%%%%%% inconsistency between models and results - for revision %%%%%%',
	'\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\n',
	'\nnot_clean_model(Model) :-',
	'\n	activity(Activity),',
	'\n	in_model(Activity, Model),',
	'\n	not active(Activity, Model).',
	'\n',
	'\nnot_clean_model(Model) :-',
	'\n	involved(Entity, Version1, Model),',
	'\n	involved(Entity, Version2, Model),',
	'\n	Version1 != Version2.',
	'\n',
	'\ninconsistent(Model, Result) :-',
	'\n	predicts(Model, Experiment, Prediction),',
	'\n	result(Result, Experiment, Outcome),',
	'\n	Prediction != Outcome,',
	'\n	relevant(Result, Model),',
	'\n	not ignored(Result).']


def model_difference_rules():
	return ['\n different(Model, ExternalModel) :-',
	'\n	model(Model),',
	'\n	activity(Activity),',
	'\n	external_model(ExternalModel),',
	'\n	in_model(Activity, Model),',
	'\n	not in_model(Activity, ExternalModel).',
	'\n',
	'\ndifferent(Model, ExternalModel) :-',
	'\n	model(Model),',
	'\n	activity(Activity),',
	'\n	external_model(ExternalModel),',
	'\n	not in_model(Activity, Model),',
	'\n	in_model(Activity, ExternalModel).']


#
# additional stuff for experiment design:
#

def export_models_exp_design(models):
	strings = []
	# model().
	joined_models = ';'.join([x.ID for x in models])
	strings.append(joined_models.join(['\nmodel(', ').']))
	# specification:
	for model in models:
		strings.extend(export_model_specification(model))

	return strings


def modeh_replacement(cost_model):
	exp_spec_elements = [e for e in export_experiment_specification_elements(cost_model).keys()]
	joined_elements = ','.join(exp_spec_elements)
	return joined_elements.join(['\n0{', '}%s.' % len(exp_spec_elements)])


def models_nr_and_probabilities(models):
	out = []
	counter = 0
	for model in models:
		out.append('\nnr(%s,%s).' % (counter, model.ID))
		out.append('\nprobability(%s, %s).' % (model.quality, model.ID))
		counter += 1
	return out


def cost_rules(cost_model):
	output = []
	cost_dict = export_experiment_specification_elements(cost_model)
	counter = 0
	for element in cost_dict.keys():
		output.append(''.join(['\ncost(%s, %s) :- ' % (cost_dict[element], counter), element, '.']))
		counter += 1
	return output


def ban_experiment(expDescription):
	exp_info = []
	# dealing with experiment types
	if isinstance(expDescription.experiment_type, exp_repr.DetectionEntity):
		exp_info.append('\n:- designed(experiment(detection_entity_exp, %s))' % expDescription.experiment_type.entity_id)
	elif isinstance(expDescription.experiment_type, exp_repr.LocalisationEntity):
		tpl = (expDescription.experiment_type.entity_id, expDescription.experiment_type.compartment_id)
		exp_info.append('\n:- designed(experiment(localisation_entity_exp, %s, %s))' % tpl)
	elif isinstance(expDescription.experiment_type, exp_repr.DetectionActivity):
		exp_info.append('\n:- designed(experiment(detection_activity_exp, %s))' % expDescription.experiment_type.activity_id)
	elif isinstance(expDescription.experiment_type, exp_repr.AdamTwoFactorExperiment):
		tpl = (expDescription.experiment_type.gene_id, expDescription.experiment_type.metabolite_id)
		exp_info.append('\n:- designed(experiment(adam_two_factor_exp, %s, %s))' % tpl)
	elif isinstance(expDescription.experiment_type, exp_repr.ReconstructionActivity):
		exp_info.append('\n:- designed(experiment(basic_reconstruction_exp, %s))' % expDescription.experiment_type.activity_id)
	elif isinstance(expDescription.experiment_type, exp_repr.ReconstructionEnzReaction):
		tpl = (expDescription.experiment_type.reaction_id, expDescription.experiment_type.enzyme_id)
		exp_info.append('\n:- designed(experiment(enz_reconstruction_exp, %s, %s))' % tpl)
	elif isinstance(expDescription.experiment_type, exp_repr.ReconstructionTransporterRequired):
		tpl = (expDescription.experiment_type.transport_activity_id, expDescription.experiment_type.transporter_id)
		exp_info.append('\n:- designed(experiment(transp_reconstruction_exp, %s, %s))' % tpl)
	else:
		raise TypeError("ban_experiment: exp description type not recognised: %s" % expDescription)

	# dealing with interventions:
	for inter in expDescription.interventions:
		if (isinstance(inter, mnm_repr.Add) and isinstance(inter.condition_or_activity, mnm_repr.Condition)):
			tpl = (inter.condition_or_activity.entity.ID, inter.condition_or_activity.entity.version, inter.condition_or_activity.compartment.ID)
			exp_info.append('add(setup_present(%s, %s, %s))' % tpl)
		elif (isinstance(inter, mnm_repr.Remove) and isinstance(inter.condition_or_activity, mnm_repr.Condition)):
			tpl = (inter.condition_or_activity.entity.ID, inter.condition_or_activity.entity.version, inter.condition_or_activity.compartment.ID)
			exp_info.append('remove(setup_present(%s, %s, %s))' % tpl)
		elif (isinstance(inter, mnm_repr.Add) and isinstance(inter.condition_or_activity, mnm_repr.Activity)): # additional import activities
			exp_info.append('add(%s)' % inter.condition_or_activity.ID)
		else:
			raise TypeError("ban_experiment: intervention type not recognised: %s" % inter)
	# formatting:
	st = ','.join(exp_info)
	return ''.join([st, '.'])


def export_experiment_specification_elements(cost_model):
	output = {}

	for element in cost_model.types.keys():
		if element == exp_repr.DetectionEntity:
			output['design_type(detection_entity_exp)'] = cost_model.types[element]
		elif element == exp_repr.AdamTwoFactorExperiment:
			output['design_type(adam_two_factor_exp)'] = cost_model.types[element]
		elif element == exp_repr.ReconstructionActivity:
			output['design_type(basic_reconstruction_exp)'] = cost_model.types[element]
		elif element == exp_repr.ReconstructionEnzReaction:
			output['design_type(enz_reconstruction_exp)'] = cost_model.types[element]
		elif element == exp_repr.ReconstructionTransporterRequired:
			output['design_type(transp_reconstruction_exp)'] = cost_model.types[element]
		elif element == exp_repr.LocalisationEntity:
			output['design_type(localisation_entity_exp)'] = cost_model.types[element]
		elif element == exp_repr.DetectionActivity:
			output['design_type(detection_activity_exp)'] = cost_model.types[element]
		else:
			raise TypeError("export_experiment_specification_elements: type not recognised: %s" % element)

	for element in cost_model.design_compartment.keys():
		output['design_compartment(%s)' % element] = cost_model.design_compartment[element]

	for element in cost_model.design_deletable.keys():
		output['design_deletable(%s)' % element.ID] = cost_model.design_deletable[element]

	for element in cost_model.design_available.keys():
		output['design_available(%s)' % element.ID] = cost_model.design_available[element]

	for element in cost_model.design_activity_rec.keys():
		output['design_activity_rec(%s)' % element.ID] = cost_model.design_activity_rec[element]

	for element in cost_model.design_activity_det.keys():
		output['design_activity_det(%s)' % element.ID] = cost_model.design_activity_det[element]

	for element in cost_model.design_entity_loc.keys():
		output['design_entity_loc(%s)' % element.ID] = cost_model.design_entity_loc[element]

	for element in cost_model.design_entity_det.keys():
		output['design_entity_det(%s)' % element.ID] = cost_model.design_entity_det[element]

	for element in cost_model.intervention_add.keys():
#		[print(type(element)) for element in cost_model.intervention_add.keys()]
		if isinstance(element.condition_or_activity, Condition):
			tup = (element.condition_or_activity.entity.ID, element.condition_or_activity.entity.version, element.condition_or_activity.compartment.ID)
			output['add(setup_present(%s, %s, %s))' % tup] = cost_model.intervention_add[element]

		elif isinstance(element.condition_or_activity, Activity): # import activities for metabolites added to medium
			output['add(%s)' % element.condition_or_activity.ID] = cost_model.intervention_add[element]

		else:
			raise TypeError("export_experiment_specification_elements: intervention_add: type not recognised: %s" % element)


	for element in cost_model.intervention_remove.keys():
		tup = (element.condition_or_activity.entity.ID, element.condition_or_activity.entity.version, element.condition_or_activity.compartment.ID)
		output['remove(setup_present(%s, %s, %s))' % tup] = cost_model.intervention_remove[element]

	return output



def constant_for_calculating_score(Int):
	return '\n\n#const n = %s.' % Int


def design_constraints_basic():
	return ['\n\ndesigned :- designed(experiment(adam_two_factor_exp, Gene, Metabolite)), gene(Gene, Ver), metabolite(Metabolite, Ver).',
	'\ndesigned :- designed(experiment(transp_reconstruction_exp, Activity, Entity)), activity(Activity), entity(Entity, Ver).',
	'\ndesigned :- designed(experiment(enz_reconstruction_exp, Activity, Entity)), activity(Activity), entity(Entity, Ver).',
	'\ndesigned :- designed(experiment(basic_reconstruction_exp, Activity)), activity(Activity).',
	'\ndesigned :- designed(experiment(detection_activity_exp, Activity)), activity(Activity).',
	'\ndesigned :- designed(experiment(localisation_entity_exp, Entity, Compartment)), entity(Entity, Ver), compartment(Compartment).',
	'\ndesigned :- designed(experiment(detection_entity_exp, Entity)), entity(Entity, Ver).',
	'\n',
	'\n:- not designed.', # design at lest one exp
	'\n',
	'\n:- designed(Experiment1), designed(Experiment2), Experiment1 != Experiment2.', # design no more than one exp
	'\n',
	'\nhas_true_model :- predicts(Model, Experiment, true), model(Model), designed(Experiment).', # designed exp must make at least
	'\nhas_false_model :- predicts(Model, Experiment, false), model(Model), designed(Experiment).',# one model false and one true
	'\n:- not has_true_model.',
	'\n:- not has_false_model.',
	'\n',
	'\n:- designed(experiment(adam_two_factor_exp, Gene, Metabolite)), add(Whatever).',
	'\n:- designed(experiment(adam_two_factor_exp, Gene, Metabolite)), remove(Whatever).', # no interventions for adam-style exps
	'\n:- involved(Entity, Version1, Model), involved(Entity, Version2, Model), Version1 != Version2.', # only one version of entity in model
	'\n',
	'\nentity_in_model(Entity, Version, Compartment, Model) :- in_model(setup_present(Entity, Version, Compartment), Model).',
	'\nentity_in_model(Entity, Version, Compartment, Model) :- synthesizable(Entity, Version, Compartment, Model).',
	'\n:- add(Activity), substrate(Ent,Ver,Comp,Activity), model(Model), not entity_in_model(Ent, Ver, Comp, Model).']



def cost_minimisation_rules():
	return ['\n\ntotal_cost(TCost) :- TCost = #sum[cost(Cost, Nr)=Cost].',
	'\n#minimize[total_cost(TCost) = TCost@1].']


def experiment_design_rules():
	return ['\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\n%%%%%% rules for exp design %%%%%%',
	'\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%',
	'\n',
	'\ndesigned(experiment(adam_two_factor_exp, Gene, Metabolite)) :-',
	'\n	design_type(adam_two_factor_exp),',
	'\n	design_deletable(Gene),',
	'\n	design_available(Metabolite).',
	'\n',
	'\ndesigned(experiment(transp_reconstruction_exp, Activity, Entity)) :-',
	'\n	design_type(transp_reconstruction_exp),',
	'\n	design_activity_rec(Activity),',
	'\n	design_available(Entity).',
	'\n',
	'\ndesigned(experiment(enz_reconstruction_exp, Activity, Entity)) :-',
	'\n	design_type(enz_reconstruction_exp),',
	'\n	design_activity_rec(Activity),',
	'\n	design_available(Entity).',
	'\n',
	'\ndesigned(experiment(basic_reconstruction_exp, Activity)) :-',
	'\n	design_type(basic_reconstruction_exp),',
	'\n	design_activity_rec(Activity).',
	'\n',
	'\ndesigned(experiment(detection_activity_exp, Activity)) :-',
	'\n	design_type(detection_activity_exp),',
	'\n	design_activity_det(Activity).',
	'\n',
	'\ndesigned(experiment(localisation_entity_exp, Entity, Compartment)) :-',
	'\n	design_type(localisation_entity_exp),',
	'\n	design_entity_loc(Entity),',
	'\n	design_compartment(Compartment).',
	'\n',
	'\ndesigned(experiment(detection_entity_exp, Entity)) :-',
	'\n	design_type(detection_entity_exp),',
	'\n	design_entity_det(Entity).']


def hide_show_statements():
	return ['\n#hide.',
	'\n#show add/1.',
	'\n#show remove/1.',
	'\n#show design_type/1.',
	'\n#show design_deletable/1.',
	'\n#show design_available/1.',
	'\n#show design_entity_det/1.',
	'\n#show design_entity_loc/1.',
	'\n#show design_compartment/1.',
	'\n#show design_activity_rec/1.',
	'\n#show design_activity_det/1.']



#def basic_exp_design_rules():  #NOT NEEDED: advanced is more general and covers this one too
#	return ['\n\nexp_score(0,1,0,0) :- indifferent(Model, Experiment), designed(Experiment), model(Model), nr(0,Model).',
#	'\nexp_score(0,0,1,0) :- predicts(Model, Experiment, true), designed(Experiment), model(Model), nr(0,Model).',
#	'\nexp_score(0,0,0,1) :- predicts(Model, Experiment, false), designed(Experiment), model(Model), nr(0,Model).',
#	'\n',
#	'\nexp_score(I,Ind+1,Tr,Fa) :- exp_score(I-1, Ind, Tr, Fa), indifferent(Model, Experiment), designed(Experiment), model(Model), nr(I, Model).',
#	'\nexp_score(I,Ind,Tr+1,Fa) :- exp_score(I-1, Ind, Tr, Fa), predicts(Model, Experiment, true), designed(Experiment), model(Model), nr(I, Model).',
#	'\nexp_score(I,Ind,Tr,Fa+1) :- exp_score(I-1, Ind, Tr, Fa), predicts(Model, Experiment, false), designed(Experiment), model(Model), nr(I, Model).',
#	'\n',
#	'\nexp_score(I) :- exp_score(I,Ind,Tr,Fa).',
#	'\n',
#	'\nfinal_score(I,Ind,Tr,Fa) :- exp_score(I,Ind,Tr,Fa), not exp_score(I+1).',
#	'\n',
#	'\nfinal_score(|Tr*10-n| + |Fa*10-n| + Ind*10) :- final_score(I,Ind,Tr,Fa).']


def advanced_exp_design_rules():
	return ['\n\nexp_score(0,Prb,0,0) :- indifferent(Model, Experiment), designed(Experiment), model(Model), nr(0,Model), probability(Prb, Model).',
	'\nexp_score(0,0,Prb,0) :- predicts(Model, Experiment, true), designed(Experiment), model(Model), nr(0,Model), probability(Prb, Model).',
	'\nexp_score(0,0,0,Prb) :- predicts(Model, Experiment, false), designed(Experiment), model(Model), nr(0,Model), probability(Prb, Model).',
	'\n',
	'\nexp_score(I,Ind+Prb,Tr,Fa) :- exp_score(I-1, Ind, Tr, Fa), indifferent(Model, Experiment), designed(Experiment), model(Model), nr(I, Model), probability(Prb, Model).',
	'\nexp_score(I,Ind,Tr+Prb,Fa) :- exp_score(I-1, Ind, Tr, Fa), predicts(Model, Experiment, true), designed(Experiment), model(Model), nr(I, Model), probability(Prb, Model).',
	'\nexp_score(I,Ind,Tr,Fa+Prb) :- exp_score(I-1, Ind, Tr, Fa), predicts(Model, Experiment, false), designed(Experiment), model(Model), nr(I, Model), probability(Prb, Model).',
	'\n',
	'\nexp_score(I) :- exp_score(I,Ind,Tr,Fa).',
	'\n',
	'\nfinal_score(I,Ind,Tr,Fa) :- exp_score(I,Ind,Tr,Fa), not exp_score(I+1).',
	'\n',
	'\nfinal_score(|Tr*10-n| + |Fa*10-n| + Ind*10) :- final_score(I,Ind,Tr,Fa).'
	'\n#minimize[final_score(Score) = Score@2].']

#
# predictions
#

def export_display_for_oracle(expDescription):
	if isinstance(expDescription.experiment_type, DetectionEntity) or isinstance(expDescription.experiment_type, LocalisationEntity):
		return ['\n#hide.', '\n#show synthesizable/4.', '\n#show initially_present/4.']
	elif isinstance(expDescription.experiment_type, DetectionActivity):
		return ['\n#hide.', '\n#show active/2.']
	elif isinstance(expDescription.experiment_type, AdamTwoFactorExperiment):
		return ['\n#hide.', '\n#show predicts/3.']
	else:
		raise TypeError("export_display_for_oracle: exp type not recognised: %" % expDescription.experiment_type)


