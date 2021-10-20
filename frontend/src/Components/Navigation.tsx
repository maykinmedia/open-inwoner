import React, { Component } from "react";

import { AppBar } from "@gemeente-denhaag/appbar";

export class LocalAppBar extends Component {
    render() {
        return (
            <AppBar position="static" color="primary">{this.props.children}</AppBar>
        )
    }
}
