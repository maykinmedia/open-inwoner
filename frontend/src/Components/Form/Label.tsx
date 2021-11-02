import './Label.scss';

interface LabelProps {
    for: string,
    children?: any
}

export function Label(props:LabelProps) {
  return (
    <label
      className="label"
      htmlFor={`id_${props.for}`}
    >
      { props.children }
    </label>
  );
}
