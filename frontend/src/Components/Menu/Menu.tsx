import './Menu.scss';

export function Menu(props:any) {
  return (
    <div className="menu">
      <nav className="menu__container">
        { props.children }
      </nav>
    </div>
  );
}
