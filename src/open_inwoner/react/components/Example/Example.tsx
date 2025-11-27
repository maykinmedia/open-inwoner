import { usePropsOrScriptData } from '@react/lib/getJsonScriptData';
import { registerWebComponent } from '@react/lib/web-component/utils';
import { FunctionComponent as FC } from 'preact';
import { WEB_COMPONENT_NAME } from '.';
import './Example.scss';

export interface IExampleDataProps {
  title: string;
  description: string;
  data_url: string;
}

export interface IExampleProps {
  dataId?: string;
  data?: IExampleDataProps[];
}

const Example: FC<IExampleProps> = ({ dataId, data }) => {
  if (!dataId && !data) return <></>;

  const actualData = usePropsOrScriptData<IExampleDataProps[]>(data, dataId);

  return (
    <div class={WEB_COMPONENT_NAME}>
      {actualData?.map(({ title, description, data_url }, i) => {
        return (
          <a href={data_url} key={i}>
            <h1>{title}</h1>
            <p>{description}</p>
          </a>
        );
      })}
    </div>
  );
};

// This wrapper allows lazy loading of the component
export function loader() {
  // @ts-expect-error The webcomponent name should be linked, i am not going to do that in this example.
  registerWebComponent(Example, WEB_COMPONENT_NAME, ['data', 'dataId'], {
    i18n: false, // With true render component inside I18nProvider.
    shadow: false,
  });
}

export default Example;
