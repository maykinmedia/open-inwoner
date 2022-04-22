import React from 'react';
import {createRoot} from 'react-dom/client';
import {
  Step,
  StepHeader,
  StepHeading,
  StepList,
  StepMarker,
  StepSection,
  SubStep,
  SubStepHeading,
  SubStepList,
  SubStepMarker,
} from '@gemeente-denhaag/process-steps';

/** @type {NodeListOf<HTMLElement>} */
const PROCESS_STEPS = document.querySelectorAll('.status-list');


/**
 * The process steps list with bot steps and sub steps.
 * @param {HTMLElement} node The target component containing data-status-list with context in JSON format.
 * @return {jsx.JSX.Element}
 */
const renderProcessSteps = (node) => {
  const json = node.dataset.statusList;
  const statusList = JSON.parse(json);

  return (
    <StepList>
      {statusList.map(renderStep)}
    </StepList>
  );
}

/**
 * A step with sub steps.
 * @param {Object} step
 * @param {number} index
 * @return {jsx.JSX.Element}
 */
const renderStep = (step, index) => {
  return (
    <Step key={index} checked={step.done} expanded={step.done}>
      <StepSection>
        <StepHeader>
          <StepMarker>
            <div>{index + 1}</div>
          </StepMarker>
          <StepHeading>{step.description}</StepHeading>
        </StepHeader>
      </StepSection>

      <SubStepList>
        {step.substatuses?.map(renderSubStep)}
      </SubStepList>
    </Step>
  );
};

/**
 * A step with sub steps.
 * @param {Object} subStep
 * @param {number} index
 * @return {jsx.JSX.Element}
 */
const renderSubStep = (subStep, index) => {
  const date = new Date(subStep.date);
  const months = ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december']
  const day = date.getDay()
  const month = months[date.getMonth()];

  return (
    <SubStep key={index}>
      <SubStepMarker> </SubStepMarker>
      <SubStepHeading>{`${day} ${month}: ${subStep.description}`}</SubStepHeading>
    </SubStep>
  );
}


// Start!
[...PROCESS_STEPS].forEach((node) => {
  const root = createRoot(node);
  root.render(renderProcessSteps(node));
});
