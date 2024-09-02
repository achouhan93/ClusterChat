import { CoreModule } from "../core-module";
import { CosmosInputNode, CosmosInputLink } from "../../types";
export declare class ForceGravity<N extends CosmosInputNode, L extends CosmosInputLink> extends CoreModule<N, L> {
    private runCommand;
    initPrograms(): void;
    run(): void;
}
