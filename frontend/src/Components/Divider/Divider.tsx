import React, { Component } from "react";

import './Divider.scss'

interface DividerProps {
}

export class Divider extends Component<DividerProps, {}> {
    render() {
        return (
            <hr className="divider" />
        )
    }
}
